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


# Setup AWS Bedrock
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")



def edit_email_section(query: str):
    messages = [HumanMessage(content=query)]

    model = ChatBedrockConverse(
        client=bedrock_rt,
        model=model_id,
        provider=provider,
        temperature=0,
        max_tokens=None,
    )

    result = model.invoke(messages)

    print(result.content)

    return result.content


nlemaildesigner__edit_email_section = Tool(
    name="NaturalLanguageHtmlEditor",
    description="Processes user-provided HTML snippets and returns modifications based on the request.",
    func=edit_email_section
)


tools = [] 
tools.append(nlemaildesigner__edit_email_section)

class NaturalLanguageHtmlEditorAgent:

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



def nlhtml_editor(query: str):
    print("nlhtml_editor: Running....")
    prompt = load_prompt('agent_nlhtml_editor_prompt.txt')
    messages = [HumanMessage(content=query)]

    model = ChatBedrockConverse(
        client=bedrock_rt,
        model=model_id,
        provider=provider,
        temperature=0,
        max_tokens=None,
    )

    abot = NaturalLanguageHtmlEditorAgent(model, tools, system=prompt)
    result = abot.graph.invoke({"messages": messages}, config={"recursion_limit": 10})

    print(result["messages"][-1].content)

    # Content parser remove thinking/response from llm
    return re.sub(r"<thinking>[\s\S]*?</thinking>", "", result["messages"][-1].content).strip() 