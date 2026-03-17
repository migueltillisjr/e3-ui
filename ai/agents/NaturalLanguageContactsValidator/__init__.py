from ai.agents.NaturalLanguageDatabase import ask_db
from .helpers import batch_validate_emails
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


def trim_request(query: str) -> str:
    prompt = f"""
Prompt:
You are a data query assistant.

Your task is to extract only the part of the user's request that describes what data to retrieve, excluding instructions, actions, or tasks.

Return a clean, concise description of the data to retrieve, suitable for use in generating a SQL query.

Example:

User Request: "Validate the first 2 contacts from the United States"

Output: "Get the first 2 contacts from the United States"

Only return the rewritten data-related query, nothing else.

User request:
{query}
    """
    body = {
        "prompt": prompt,
        "max_tokens": 300,
        "temperature": 0.2
    }

    model = ChatBedrockConverse(
        client=bedrock_rt,
        model=model_id,
        provider=provider,
        temperature=0,
        max_tokens=None,
    )
    
    response = model.invoke(json.dumps(body))
    output = response.content
    return output

# Tools
def tool_nl_validate_contacts(query: str) -> str:
    print("Validating contacts...")
    query = trim_request(query)
    print("**trimmed request**")
    print(query)

    db_output = ask_db(query=query, chunk_size=200)
    print(db_output)

    batch_validate_emails(query=query)

    return f"Successfully validated for request: {query}. email@example.com"


nl_email_validate_contacts_tool = Tool(
    name="NaturalLanguageValidateContacts",
    description="Validate contacts.",
    func=tool_nl_validate_contacts
)


tools = [] 
tools.append(nl_email_validate_contacts_tool)


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
        # Only evaluate if action hasn't run
        if state.get("action_ran"):
            print("exists_action: Action already ran...")
            return False
        else:
            result = state["messages"][-1]
            return len(result.tool_calls) > 0

    def action_ran(self, state: AgentState):
        # Only evaluate if action hasn't run
        if state.get("action_ran", False):
            print("exists_action: Action already ran...")
            return True
        else:
            return False

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
                print("**Tool result**")
                print(result)
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


def validate_contacts(query: str):
    print(f"Validating contacts: {query}")
    prompt = load_prompt('neverbounce.txt')
    print(trim_request(query))
    messages = [HumanMessage(content=query)]

    model = ChatBedrockConverse(
        client=bedrock_rt,
        model=model_id,
        provider=provider,
        temperature=0,
        max_tokens=None,
    )

    abot = Agent(model, tools, system=prompt)
    result = abot.graph.invoke({"messages": messages}, config={"recursion_limit": 35})

    print(result["messages"][-1].content)

    return result

    