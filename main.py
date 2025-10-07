from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from datetime import datetime
import json
import uuid
from typing import List, Dict, Any, Optional
import pprint

from langchain_core.messages import HumanMessage, SystemMessage

from agent import create_agent
from models.schemas import ChatRequest, OpenAIMessage, OpenAIChatRequest
from config import SYSTEM_MESSAGE

# ---------------------------
# FastAPI app
# ---------------------------
app = FastAPI()


# ---------------------------
# Create Agent
# ---------------------------
app_graph = create_agent()


# ---------------------------
# Endpoints
# ---------------------------

@app.get("/")
async def root():
    return {"message": "LangGraph + Ollama server is running."}


@app.post("/chat")
async def chat(req: ChatRequest):
    """Original endpoint - Stream the assistant's final response token by token."""

    initial_state = {
        "messages": [
            SystemMessage(content=SYSTEM_MESSAGE),
            HumanMessage(content=req.message)
        ]
    }

    async def token_generator():
        try:
            async for event in app_graph.astream_events(initial_state, version="v1"):
                if event["event"] == "on_chat_model_stream":
                    data = event.get("data")
                    if isinstance(data, dict):
                        chunk = data.get("chunk")
                        if chunk and hasattr(chunk, "content"):
                            for part in chunk.content:
                                if isinstance(part, dict):
                                    if part.get("type") == "text":
                                        yield part["text"]
                                elif isinstance(part, str):
                                    yield part
        except Exception as e:
            yield f"\n[Error: {str(e)}]\n"

    return StreamingResponse(token_generator(), media_type="text/plain")

@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    """OpenAI-compatible endpoint for Open WebUI integration."""

    # Extract the user's message from the OpenAI format
    user_message = ""
    system_message = SYSTEM_MESSAGE

    for msg in request.messages:
        if msg.role == "system":
            system_message = msg.content
        elif msg.role == "user":
            user_message = msg.content

    print("\n🧠 [DEBUG] Incoming system message:")
    pprint.pprint(system_message)
    print("\n💬 [DEBUG] Incoming user message:")
    pprint.pprint(user_message)

    initial_state = {
        "messages": [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ]
    }

    print("\n📦 [DEBUG] Initial agent state:")
    pprint.pprint(initial_state)

    async def openai_stream_generator():
        chunk_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"

        initial_chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(datetime.now().timestamp()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "delta": {
                    "role": "assistant",
                    "content": ""
                },
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(initial_chunk)}\n\n"

        try:
            async for event in app_graph.astream_events(initial_state, version="v1"):
                print("\n📡 [DEBUG] Received event:")
                pprint.pprint(event)

                if event["event"] == "on_chat_model_stream":
                    data = event.get("data")
                    if isinstance(data, dict):
                        chunk = data.get("chunk")
                        print("\n🧩 [DEBUG] Chunk object:")
                        pprint.pprint(chunk)

                        if chunk and hasattr(chunk, "content"):
                            for part in chunk.content:
                                content_text = ""
                                if isinstance(part, dict):
                                    if part.get("type") == "text":
                                        content_text = part["text"]
                                elif isinstance(part, str):
                                    content_text = part

                                print("\n📝 [DEBUG] Extracted content text:")
                                pprint.pprint(content_text)

                                if content_text:
                                    response_chunk = {
                                        "id": chunk_id,
                                        "object": "chat.completion.chunk",
                                        "created": int(datetime.now().timestamp()),
                                        "model": request.model,
                                        "choices": [{
                                            "index": 0,
                                            "delta": {
                                                "content": content_text
                                            },
                                            "finish_reason": None
                                        }]
                                    }
                                    yield f"data: {json.dumps(response_chunk)}\n\n"

            final_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            print("\n✅ [DEBUG] Final chunk:")
            pprint.pprint(final_chunk)

            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            print("\n❌ [ERROR] Exception occurred:")
            pprint.pprint(str(e))

            error_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "content": f"\n[Error: {str(e)}]\n"
                    },
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        openai_stream_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@app.get("/v1/models")
async def list_models():
    """OpenAI-compatible models endpoint."""
    return {
        "object": "list",
        "data": [
            {
                "id": "qwen2.5:7b",
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "local"
            }
        ]
    }


# ---------------------------
# Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
# ---------------------------