from ai.agents.NaturalLanguageDatabase import ask_db
from ai.agents.NaturalLanguageEmailDesigner import ask_email_designer
from ai.agents.NaturalLanguageContactsValidator import validate_contacts
from ai.agents.NaturalLanguageHtmlEditor import nlhtml_editor
import sys
import csv
import os
from .load_prompt import load_prompt
from .utils import utils
from .utils.libs import *
from dotenv import load_dotenv



# Load environment variables from .env
load_dotenv()



# Set basic configs
logger = utils.set_logger()
pp = utils.set_pretty_printer()

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

# Validate PostgreSQL DB funtionality
engine = create_engine(db_url)


# Setup PostgreSQL
engine = create_engine(os.getenv("DB_URL"))

# Setup AWS Bedrock
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")


nlemaildesigner__ask_email_designer = Tool(
    name="NaturalLanguageEmailDesigner",
    description="Transforms natural language requests into edits that modify complete HTML email designs. Accepts full HTML input for end-to-end customization.",
    func=ask_email_designer
)

nlemaildesigner__edit_email_section = Tool(
    name="NaturalLanguageHtmlEditor",
    description="Processes user-provided HTML snippets and returns recommended modifications based on the request.",
    func=nlhtml_editor
)

nldb__ask_db = Tool(
    name="NaturalLanguageContactsDatabase",
    description="Translates natural language questions into SQL queries and returns relevant contact data from the database.",
    func=ask_db
)

nldb__validate_contacts = Tool(
    name="NaturalLanguageValidateContacts",
    description="Queries the DB to get contacts, then validates contact records to ensure accuracy and deliverability. Filters out invalid or low-quality entries to prevent wasted effort and resources on marketing campaigns.",
    func=validate_contacts
)

tools = [] 
tools.append(nldb__ask_db)
# tools.append(nlemaildesigner__ask_email_designer)
tools.append(nlemaildesigner__edit_email_section)
tools.append(nldb__validate_contacts)



class Agent:

    def __init__(self, model, tools, system=""):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_bedrock)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges(
            "llm", self.exists_action, {True: "action", False: END}
        )
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def exists_action(self, state: AgentState):
        result = state["messages"][-1]
        return len(result.tool_calls) > 0

    def call_bedrock(self, state: AgentState):
        messages = state["messages"]
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {"messages": [message]}

## Parallel Tool Call
    def take_action(self, state: AgentState):
        tool_calls = state["messages"][-1].tool_calls
        results: List[ToolMessage] = []
    
        def call_tool(t) -> ToolMessage:
            if t["name"] not in self.tools:
                print("\n ....bad tool name....")
                result = "bad tool name, retry"
            else:
                result = self.tools[t["name"]].invoke(t["args"])
            return ToolMessage(tool_call_id=t["id"], name=t["name"], content=str(result))
    
        with ThreadPoolExecutor(max_workers=len(tool_calls)) as executor:
            futures = {executor.submit(call_tool, t): t for t in tool_calls}
            for future in as_completed(futures):
                try:
                    tool_result = future.result()
                    results.append(tool_result)
                except Exception as e:
                    t = futures[future]
                    print(f"Error in tool call {t['name']}: {e}")
                    results.append(
                        ToolMessage(tool_call_id=t["id"], name=t["name"], content="tool call failed")
                    )
    
        print("Thinking..")
        return {"messages": results}



def route_ai_request(query: str):
    prompt = load_prompt('agent_router_prompt.txt')
    messages = [HumanMessage(content=query)]

    model = ChatBedrockConverse(
        client=bedrock_rt,
        model=model_id,
        provider=provider,
        temperature=0,
        max_tokens=None,
    )

    abot = Agent(model, tools, system=prompt)
    result = abot.graph.invoke({"messages": messages}, config={"recursion_limit": 10})

    print(result["messages"][-1].content)
    # Content parser remove thinking/response from llm
    return re.sub(r"<thinking>[\s\S]*?</thinking>", "", result["messages"][-1].content).strip() 