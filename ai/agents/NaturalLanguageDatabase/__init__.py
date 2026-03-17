import csv
import os
from .load_prompt import load_prompt
from .utils import utils
from .utils.libs import *
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

CONTACTS_DIR = os.getenv("CONTACTS_DIR")

db_schema = load_prompt('db_schema.sql')

prompt = load_prompt('prompt.txt', context={
    "db_schema": db_schema
})

# Set basic configs
logger = utils.set_logger()
pp = utils.set_pretty_printer()

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

# Validate PostgreSQL DB funtionality
engine = create_engine(db_url)

# Setup PostgreSQL
engine = create_engine(os.getenv("DB_URL"))


def write_contacts_to_tsv(rows, filename="contacts.tsv"):
    output_dir = os.path.join(CONTACTS_DIR)
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, filename)

    with open(output_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ TSV written to {output_path}")
    return output_path


def postgress_sql(sql_query: str, params: dict = None):
    """
    Execute a SQL query with optional parameters.
    """
    print(sql_query)
    with engine.connect() as conn:
        try:
            result = conn.execute(text(sql_query), params or {})
            conn.commit()
            print("!!! postgres_sql result")
            print(result)
            return result
        except Exception as e:
            print(f"DB Error: {str(e)}")
            return None


def nldbpostgress_sql(sql_query: str):
    # Connect and query
    with engine.connect() as conn:
        try:
            result = conn.execute(text(sql_query))
            rows = result.mappings().all()  # Convert result rows to dicts
            # return rows  # Print the result list
            write_contacts_to_tsv(rows=rows)
            output_dir = CONTACTS_DIR
            return f"Row count {len(rows)} written to location {output_dir}"
        except Exception as e:
            print(f"DB Error: {str(e)}")

# Setup AWS Bedrock
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

def tool_nl_to_sql(query: str) -> str:
    print("True query...")
    print(query)
    prompt = f"Convert the following natural language question to a SQL query and only return the sql as a basic string, not markup:\n\n{query}\n\n"
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
    return nldbpostgress_sql(str(output).replace("```sql", "").replace("```", ""))


nldbpostgres_to_sql_tool = Tool(
    name="NaturalLanguageToSQL",
    description="Converts natural language questions into SQL queries.",
    func=tool_nl_to_sql
)


tools = [] 
tools.append(nldbpostgres_to_sql_tool)


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


def split_tsv_file(filepath, chunk_size=200):
    base_dir = os.path.dirname(filepath)
    filename = os.path.splitext(os.path.basename(filepath))[0]

    with open(filepath, 'r', encoding='utf-8') as f:
        header = f.readline()  # Keep the header line
        lines = f.readlines()

    for i in range(0, len(lines), chunk_size):
        chunk_lines = lines[i:i+chunk_size]
        chunk_number = (i // chunk_size) + 1
        output_filename = f"{filename}.{chunk_number}.chunked.tsv"
        output_path = os.path.join(base_dir, output_filename)

        with open(output_path, 'w', encoding='utf-8') as chunk_file:
            chunk_file.write(header)
            chunk_file.writelines(chunk_lines)

        print(f"✅ Wrote {output_path} ({len(chunk_lines)} lines)")



def ask_db(query: str, chunk_size: int = None, db_export_file_path="contacts.tsv"):
    output_dir = CONTACTS_DIR
    output_path = os.path.join(output_dir, db_export_file_path)
    messages = [HumanMessage(content=query)]

    model = ChatBedrockConverse(
        client=bedrock_rt,
        model=model_id,
        provider=provider,
        temperature=0,
        max_tokens=None,
    )
    abot = Agent(model, tools, system=prompt)
    result = abot.graph.invoke({"messages": messages})

    if chunk_size:
        split_tsv_file(filepath=output_path, chunk_size=chunk_size)
        os.remove(output_path)

    print(result["messages"][-1].content)
    return result["messages"][-1].content
    # return "<!-- Request Complete -->"


