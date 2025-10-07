from langchain_core.tools import tool
from datetime import datetime
import os


@tool
def get_current_time() -> str:
    """Get the current date and time in a human-readable string."""
    return datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")


@tool
def get_filesystem(path: str) -> str:
    """List the files and directories at the given filesystem path."""
    try:
        return str(os.listdir(path))
    except Exception as e:
        return f"Error accessing path '{path}': {e}"