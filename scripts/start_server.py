import os
import gc
import psutil
import yaml
from fastapi import FastAPI, HTTPException
import uvicorn
from typing import Dict, Any
import logging
from logging.handlers import RotatingFileHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_logging(config: Dict[str, Any]):
    log_config = config.get("logging", {})
    log_dir = log_config.get("log_dir", "/workspace/logs")
    os.makedirs(log_dir, exist_ok=True)
    
    handler = RotatingFileHandler(
        f"{log_dir}/server.log",
        maxBytes=int(1e8),  # 100MB
        backupCount=5
    )
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

print(f"CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES', 'Not set')}")

try:
    from llama_cpp import llama_cpp
    print(f"llama.cpp CUDA support: {llama_cpp.llama_supports_gpu_offload()}")
except Exception as e:
    logger.error(f"Could not check CUDA support: {e}")

def check_resource_usage():
    """Monitor system resource usage"""
    mem = psutil.virtual_memory()
    logger.info(f"RAM Usage: {mem.percent}%")
    
    try:
        gpu_mem = psutil.gpu_memory()
        logger.info(f"GPU Memory Usage: {gpu_mem.percent}%")
    except:
        pass  # GPU monitoring not available

# Load configuration
with open("/workspace/configs/server_config.yaml", "r") as f:
    config = yaml.safe_load(f)

MODEL_PATH = config.get("model_name")
API_HOST = config["api"].get("host", "0.0.0.0")
API_PORT = config["api"].get("port", 8000)

# Initialize FastAPI
app = FastAPI(title="Local LLM Server")

# Global variable to store model
llm = None

@app.on_event("startup")
async def load_model():
    global llm
    try:
        print(f"Loading model from: {MODEL_PATH}")
        print(f"File exists: {os.path.exists(MODEL_PATH) if MODEL_PATH else 'No path specified'}")
        
        if not MODEL_PATH:
            print("ERROR: No model path specified in config")
            return
            
        llm = Llama(
            model_path=MODEL_PATH,
            n_gpu_layers=-1,      # Offload all layers to GPU
            n_ctx=2048,           # Increase context
            n_batch=512,          # Batch size for processing
            verbose=True          # To see GPU usage
        )
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Failed to load model: {e}")
        import traceback
        traceback.print_exc()

@app.get("/generate")
def generate_text(prompt: str):
    if llm is None:
        return {"error": "Model not loaded"}
    
    try:
        # Format for Mistral Instruct
        formatted_prompt = f"<s>[INST] {prompt} [/INST]"
        
        response = llm(
            formatted_prompt,
            max_tokens=150,
            temperature=0.7,
            stop=["</s>"]
        )
        
        return {"result": response["choices"][0]["text"].strip()}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": llm is not None}

if __name__ == "__main__":
    uvicorn.run(app, host=API_HOST, port=API_PORT)
