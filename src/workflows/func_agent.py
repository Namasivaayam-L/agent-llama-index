# setup Phoenix
import json
from typing import Any, List
from config.logging import logger

from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from phoenix.otel import register

tracer_provider = register(endpoint="http://localhost:6006/v1/traces")
LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)


from llama_index.llms.groq import Groq
from llama_index.storage.chat_store.redis import RedisChatStore
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools.types import BaseTool
from llama_index.core.workflow import Workflow, StartEvent, StopEvent, step
from llama_index.core.llms.function_calling import FunctionCallingLLM

from llama_deploy import (
    deploy_workflow,
    WorkflowServiceConfig,
    ControlPlaneConfig,
)

from src.workflows.tools import tools, tools_needing_approval
from src.utils.llms import models
from src.utils.pydantic_models import *


class FuncAgentWorkflow(Workflow):
    def __init__(
        self,
        *args: Any,
        tools: list = None,
        tools_needing_approval: list = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        logger.info("Initializing FuncAgentWorkflow")
        self.tools = tools or []
        self.user_id = None
        self.tools_needing_approval = tools_needing_approval or []

        self.sources = []
        logger.info("FuncAgentWorkflow initialized")

    @step
    async def prepare_chat_history(self, ev: StartEvent) -> InputEvent:
        logger.info("Starting prepare_chat_history step")
        # clear sources
        self.sources = []
        logger.info("Cleared sources")
        
        self.input = json.loads(ev.get("input", "{}"))
        logger.info(f"Input received: {self.input}")
        
        self.llm = models[ev.get("model", "llama-3.3-70b-versatile")]
        logger.info(f"Using LLM model: {ev.get('model', 'llama-3.3-70b-versatile')}")
        
        assert self.llm.metadata.is_function_calling_model

        self.chat_store = RedisChatStore(redis_url="redis://localhost:6379", ttl=300)
        logger.info("Initialized RedisChatStore")

        self.user_id = ev.get("user_id", None)
        if not self.user_id:
            logger.error("user_id not provided")
            raise ValueError("user_id not provided")
        logger.info(f"User ID: {self.user_id}")

        self.session_id = ev.get("session_id", None)
        if not self.session_id:
            logger.error("session_id not provided")
            raise ValueError("session_id not provided")
        logger.info(f"Session ID: {self.session_id}")

        self.memory = ChatMemoryBuffer.from_defaults(
            chat_store=self.chat_store,
            chat_store_key=f"{self.user_id}:{self.session_id}",
            llm=self.llm,
        )
        logger.info("Initialized ChatMemoryBuffer")

        # get user input
        user_input = self.input.get(
            "query",
            "Please ask the user to give an input query, to start the conversation.",
        )
        user_msg = ChatMessage(role="user", content=user_input)
        self.memory.add_message(user_msg)
        logger.info("Added user message to memory")

        # get chat history
        chat_history = self.memory.get()
        logger.info("Retrieved chat history from memory")
        logger.info("Completed prepare_chat_history step")
        return InputEvent(input=chat_history)

    @step
    async def handle_llm_input(self, ev: InputEvent) -> ToolCallEvent | StopEvent:
        logger.info("Starting handle_llm_input step")
        chat_history = ev.input
        logger.info("Chat history retrieved")

        response = await self.llm.achat_with_tools(
            self.tools, chat_history=chat_history
        )
        logger.info("LLM response received")
        self.memory.add_message(response.message)
        logger.info("Added LLM message to memory")

        tool_calls = self.llm.get_tool_calls_from_response(
            response, error_on_no_tool_call=False
        )
        logger.info(f"Tool calls detected: {tool_calls}")

        if not tool_calls:
            logger.info("No tool calls detected, returning StopEvent")
            return StopEvent(result={"response": response, "sources": [*self.sources]})
        else:
            logger.info("Tool calls detected, returning ToolCallEvent")
            return ToolCallEvent(tool_calls=tool_calls)

    @step
    async def handle_tool_calls(self, ev: ToolCallEvent) -> InputEvent:
        logger.info("Starting handle_tool_calls step")
        tool_calls = ev.tool_calls
        logger.info(f"Received tool calls: {tool_calls}")
        tools_by_name = {tool.metadata.get_name(): tool for tool in self.tools}

        tool_msgs = []
        logger.info("Starting tool execution loop")
        # call tools -- safely!
        for tool_call in tool_calls:
            tool = tools_by_name.get(tool_call.tool_name)
            additional_kwargs = {
                "tool_call_id": tool_call.tool_id,
                "name": tool.metadata.get_name(),
            }
            if not tool:
                logger.warning(f"Tool {tool_call.tool_name} does not exist")
                tool_msgs.append(
                    ChatMessage(
                        role="tool",
                        content=f"Tool {tool_call.tool_name} does not exist",
                        additional_kwargs=additional_kwargs,
                    )
                )
                continue
            logger.info(f"Executing tool: {tool.metadata.get_name()}")
            try:
                tool_output = tool(**tool_call.tool_kwargs)
                self.sources.append(tool_output)
                logger.info(
                    f"Tool {tool.metadata.get_name()} output: {tool_output.content}"
                )
                tool_msgs.append(
                    ChatMessage(
                        role="tool",
                        content=tool_output.content,
                        additional_kwargs=additional_kwargs,
                    )
                )
            except Exception as e:
                logger.error(f"Encountered error in tool call: {e}")
                tool_msgs.append(
                    ChatMessage(
                        role="tool",
                        content=f"Encountered error in tool call: {e}",
                        additional_kwargs=additional_kwargs,
                    )
                )
        logger.info("Completed tool execution loop")
        for msg in tool_msgs:
            self.memory.put(msg)
        logger.info("Added tool messages to memory")

        chat_history = self.memory.get()
        logger.info("Retrieved chat history from memory")
        logger.info("Completed handle_tool_calls step")
        return InputEvent(input=chat_history)


def build_func_agent_workflow() -> FuncAgentWorkflow:
    return FuncAgentWorkflow(timeout=180, verbose=True)


async def deploy_func_agent_workflow():
    func_agent_workflow = build_func_agent_workflow()

    await deploy_workflow(
        func_agent_workflow,
        workflow_config=WorkflowServiceConfig(
            host="0.0.0.0", port=8002, service_name="func_agent_workflow"
        ),
        control_plane_config=ControlPlaneConfig(host="0.0.0.0"),
    )


# async def main():
#         agent = FuncAgentWorkflow(
#             llm= None , tools=tools, tools_needing_approval=tools[:2], timeout=120, verbose=True
#         )

#         ret = await agent.run(input="I wanna fetch all the customer data with the account name starting with 'A'")

#         print(ret["response"])


# if __name__ == "__main__":
#     import asyncio, time

#     # time.sleep(5)

#     # asyncio.run(deploy_func_agent_workflow())
#     asyncio.run(main())
