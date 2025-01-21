from llama_index.core.workflow.handler import WorkflowHandler
from llama_index.core.workflow.events import (
    InputRequiredEvent,
    HumanResponseEvent
)

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

import uuid, json
from src.workflows.func_agent import FuncAgentWorkflow
from src.workflows.tools import tools, tools_needing_approval
from src.utils.pydantic_models import RequestBody
from config.logging import logger

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/chat")
async def chat_with_bot(websocket: WebSocket):
    await websocket.accept()
    
    func_agent_workflow = FuncAgentWorkflow(tools=tools, tools_needing_approval=tools_needing_approval, timeout=None, verbose=True)
    
    try:
        while True:
            request: RequestBody = RequestBody(**(await websocket.receive_json()))
            
            if request.input.query in ["exit", "quit", "bye"]:
                break
            
            if request.session_id is None:
                request.session_id = str(uuid.uuid4())
            
            logger.info(f"Received request: {request}, {type(request)}")
            handler: WorkflowHandler = func_agent_workflow.run(
                model="gpt-4o-mini",
                # model="llama-3.1-8b-instant",
                # model="mixtral-8x7b-32768",
                # model="llama-3.3-70b-versatile",
                user_id=request.user_id,
                session_id=request.session_id,
                input=request.input.model_dump_json(),
            )

            # now we handle events coming back from the workflow
            async for event in handler.stream_events():
                logger.info(f"Received event: {event}")
                # if we get an InputRequiredEvent, that means the workflow needs human input
                if isinstance(event, InputRequiredEvent):
                    await websocket.send_json({
                        "message": event.payload,
                        "session_id": request.session_id
                    })
                    # we expect the next thing from the socket to be human input
                    request: RequestBody = RequestBody(**(await websocket.receive_json()))
                    # which we send back to the workflow as a HumanResponseEvent
                    handler.ctx.send_event(HumanResponseEvent(response=request.input.query))
            # this only happens when the workflow is complete
            model_output = await handler
            model_output = json.loads(model_output)
            logger.info(
                f"Model output generated successfully. modelOutput: {type(model_output)}, {model_output['response']}"
            )
            await websocket.send_json({
                "session_id": request.session_id,
                "message": model_output['response'],
                "tool_outputs": model_output.get('tool_outputs', None),
            })
    except Exception as e:
        logger.error(f"Error in model generation: {str(e)}")
        await websocket.send_json({"type": "error", "payload": str(e)})
    finally:
        await websocket.close()