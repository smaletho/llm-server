from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from tools import ALL_TOOLS
from config import OLLAMA_BASE_URL, OLLAMA_MODEL


def create_agent(tool_set=None):
    """
    Create a ReAct agent with specified tools.
    
    Args:
        tool_set: List of tools to use. If None, uses ALL_TOOLS.
    
    Returns:
        Configured agent graph
    """
    model = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
    
    tools = tool_set if tool_set is not None else ALL_TOOLS
    
    return create_react_agent(model, tools)