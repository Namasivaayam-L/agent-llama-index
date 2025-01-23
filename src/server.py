from llama_index.core.workflow.handler import WorkflowHandler
from llama_index.core.workflow.events import (
    InputRequiredEvent,
    HumanResponseEvent
)
from llama_index.storage.chat_store.redis import RedisChatStore
from llama_index.core.llms import ChatMessage

from typing import List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import uuid, json
from src.workflows.func_agent import FuncAgentWorkflow
from src.workflows.tools import tools, tools_needing_approval
from src.utils.pydantic_models import RequestBody, ChatResponse # Add ChatResponse
from config.logging import logger

chat_store = RedisChatStore(redis_url="redis://localhost:6379", db=0)

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

func_agent_workflow = FuncAgentWorkflow(tools=tools, tools_needing_approval=tools_needing_approval, chat_store=chat_store, timeout=None, verbose=True)

@app.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: RequestBody):
    """
    Handles chat requests and returns a response.
    """

    if request.session_id is None:
        request.session_id = str(uuid.uuid4())

    logger.info(f"Received request: {request}")

    try:
        model_output = await func_agent_workflow.run(
            model="gpt-4o-mini",
            # model="llama-3.1-8b-instant",
            # model="mixtral-8x7b-32768",
            # model="llama-3.3-70b-versatile",
            user_id=request.user_id,
            session_id=request.session_id,
            input=request.input.model_dump_json(),
        )

        model_output = json.loads(model_output)
        logger.info(f"Model output generated successfully: {model_output}")

        return ChatResponse(
            session_id=request.session_id,
            message=model_output.get('response', "Model returned No response"),
            tool_id=model_output.get('tool_id', None),
        )

    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions to be handled by FastAPI

def format_chat_history(chat_history: List[ChatMessage]) -> List[Dict[str, str]]:
    formatted_history = []
    for message in chat_history:
        text_blocks = [block for block in message.blocks if block.block_type == 'text']
        if text_blocks: # check if the list is not empty
            text_content = "".join([block.text for block in text_blocks]) # extract the text
            formatted_history.append({"role": message.role.value, "message": text_content})
    return formatted_history

@app.get('/sessions/user/{user_id}', response_model=List[str])
async def get_sessions(user_id: str):
    try:
        keys = chat_store.get_keys()
        prefix = f"{user_id}_"
        sessions = [item[len(prefix):] for item in keys if item.startswith(prefix)]
        return sessions
    except Exception as e:
        logger.error(f"Error getting sessions: {str(e)}")
        return []

@app.get('/sessions/{user_id}/{session_id}', response_model=List[Dict[str, str]])
async def get_sessions(user_id: str, session_id: str):
    try:
        messages = chat_store.get_messages(f"{user_id}_{session_id}")
        return format_chat_history(messages)
    except Exception as e:
        logger.error(f"Error getting messages from session {session_id} for user {user_id}: {str(e)}")
        return []
