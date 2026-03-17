# apt-get install graphviz graphviz-dev -y
# make sure to install pygraphviz if you haven't done so already using 'conda install --channel conda-forge pygraphviz'
from IPython.display import Image
from dotenv import load_dotenv
import json
import os
import re
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import boto3
from botocore.config import Config
from sqlalchemy import create_engine, text
from langchain_core.tools import Tool
import operator
from typing import Annotated, TypedDict

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph


warnings.filterwarnings("ignore")
import logging

# import local modules
dir_current = os.path.abspath("")
dir_parent = os.path.dirname(dir_current)
print(dir_current)
if dir_parent not in sys.path:
    sys.path.append(dir_parent)
# from utils import utils



print(f"ENV: {dir_current}/.env")
# Load environment variables from .env file or Secret Manager
load_dotenv()
aws_region = os.getenv("AWS_REGION")
model=os.getenv("MODEL")
provider=os.getenv("PROVIDER")
print(model)
print(provider)
aws_account_id = os.getenv("AWS_ACCOUNT_ID")
db_url = os.getenv("DB_URL")


# Set bedrock configs
bedrock_config = Config(
    connect_timeout=120, read_timeout=120, retries={"max_attempts": 0}
)

# Create a bedrock runtime client
bedrock_rt = boto3.client(
    "bedrock-runtime", region_name=aws_region, config=bedrock_config
)

# Create a bedrock client to check available models
bedrock = boto3.client("bedrock", region_name=aws_region, config=bedrock_config)



# claude_model_id="arn:aws:bedrock:us-west-2:509499992346:inference-profile/us.anthropic.claude-3-sonnet-20240229-v1:0"
model_id=f"arn:aws:bedrock:{aws_region}:{aws_account_id}:inference-profile/{model}"