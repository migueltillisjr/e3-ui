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

# Tools

def tool_nl_to_email_html(query: str) -> str:
    print("True query...")
    print(query)
    prompt = f"Convert the following natural language to an html email design and return as a basic string, not markup:\n\n{query}\n\n"
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


nl_email_design_tool = Tool(
    name="NaturalLanguageEmailDesign",
    description="Converts natural language questions into HTML email designs.",
    func=tool_nl_to_email_html
)


tools = [] 
tools.append(nl_email_design_tool)


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



def ask_email_designer(query: str):
    reference_email_design = load_prompt('reference_email_design.html')

    prompt = load_prompt('whole-design-prompt.txt', context={
        "reference_email_design": reference_email_design
    })
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