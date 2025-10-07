import os

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://192.168.86.45:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# System message for the agent
SYSTEM_MESSAGE = """You are a helpful assistant with access to several tools. 
Use them when necessary, but only return the final answer to the user."""