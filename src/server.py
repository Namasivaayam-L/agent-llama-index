from llama_deploy import LlamaDeployClient
from llama_deploy import (
    LlamaDeployClient,
    AsyncLlamaDeployClient,
    ControlPlaneConfig,
)

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from src.utils.pydantic_models import RequestBody
import json
import uuid
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

llama_deploy_aclient = LlamaDeployClient(ControlPlaneConfig(), timeout=180)


@app.post("/chat")
def chat_with_bot(user_message: RequestBody):

    if user_message.session_id is None:
        user_message.session_id = str(uuid.uuid4())

    session = llama_deploy_aclient.get_or_create_session(user_message.session_id)
    try:
        model_output = session.run(
            "func_agent_workflow",
            # model="mixtral-8x7b-32768",
            model="llama-3.3-70b-versatile",
            user_id=user_message.user_id,
            session_id=user_message.session_id,
            input=user_message.input.model_dump_json(),
        )
        if not model_output:
            logger.error("Model output is empty")
            raise HTTPException(
                status_code=500, detail="Model failed to generate output"
            )
        logger.info(
            f"Model output generated successfully. modelOutput: {model_output}"
        )
        # model_output = json.loads(model_output)
        return {"messages": model_output, "session_id": user_message.session_id}
    except Exception as e:
        logger.error(f"Error in model generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating model output")
