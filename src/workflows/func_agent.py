# setup Phoenix
import json
from typing import Any, List
from config.logging import logger

from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from phoenix.otel import register

tracer_provider = register(endpoint="http://localhost:6006/v1/traces")
LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)

from llama_index.storage.chat_store.redis import RedisChatStore
from llama_index.core.llms import ChatMessage
from llama_index.core.tools.types import BaseTool
from llama_index.core.workflow import (
    Workflow,
    Context,
    StartEvent,
    StopEvent,
    step,
    InputRequiredEvent,
    HumanResponseEvent,
)
from llama_index.core.llms.function_calling import FunctionCallingLLM

from src.utils.func_tool_with_ctx import FunctionToolWithContext
from src.utils.llms import models
from src.utils.pydantic_models import *


class FuncAgentWorkflow(Workflow):
    def __init__(
        self,
        *args: Any,
        tools: list[BaseTool] = None,
        tools_needing_approval: list[BaseTool] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        logger.info("Initializing FuncAgentWorkflow")
        self.tools = tools or []
        self.user_id = None
        self.tools_needing_approval = tools_needing_approval or []
        self.tool_outputs = []
        self.sources = []
        logger.info("FuncAgentWorkflow initialized")

    @step
    async def prepare_chat_history(self, ctx: Context, ev: StartEvent) -> InputEvent:
        logger.info("Starting prepare_chat_history step")
        # clear sources
        self.sources = []
        logger.info("Cleared sources")

        self.input = json.loads(ev.get("input", "{}"))
        logger.info(f"Input received: {self.input}")

        self.llm = models[ev.get("model", "llama-3.3-70b-versatile")]
        logger.info(f"Using LLM model: {ev.get('model', 'llama-3.3-70b-versatile')}")

        assert self.llm.metadata.is_function_calling_model and isinstance(
            self.llm, FunctionCallingLLM
        )

        self.chat_store = RedisChatStore(redis_url="redis://localhost:6379", ttl=300)
        logger.info("Initialized RedisChatStore")

        self.user_id = ev.get("user_id", None)
        if not self.user_id:
            logger.error("user_id not provided")
            raise ValueError("user_id not provided")
        await ctx.set("user_id", self.user_id)
        logger.info(f"User ID: {self.user_id}")

        self.session_id = ev.get("session_id", None)
        if not self.session_id:
            logger.error("session_id not provided")
            raise ValueError("session_id not provided")
        logger.info(f"Session ID: {self.session_id}")

        # get user input
        user_input = self.input.get(
            "query",
            "Please ask the user to give an input query, to start the conversation.",
        )

        if self.input.get("customer_data", None):
            await ctx.set("customer_data", self.input.get("customer_data"))
            logger.info(f"Customer data: {self.input.get('customer_data')}")

        self.chat_store_key = f"{self.user_id}-{self.session_id}"
        logger.info(f"Chat store key: {self.chat_store_key}")

        user_msg = ChatMessage(role="user", content=user_input)
        self.chat_store.add_message(self.chat_store_key, user_msg)
        logger.info("Added user message to memory")

        # get chat history
        chat_history = self.chat_store.get_messages(self.chat_store_key)
        logger.info("Completed prepare_chat_history step")
        return InputEvent(input=chat_history)

    @step
    async def handle_llm_input(
        self, ctx: Context, ev: InputEvent
    ) -> ToolCallEvent | InputRequiredEvent | StopEvent:
        logger.info("Starting handle_llm_input step")
        chat_history = ev.input
        logger.info(f"Chat history retrieved before llm call, {chat_history}")

        response = await self.llm.achat_with_tools(
            self.tools, chat_history=chat_history
        )
        logger.info(f"LLM response received {response}")


        tool_calls = self.llm.get_tool_calls_from_response(
            response, error_on_no_tool_call=False
        )
        logger.info(f"Tool calls detected: {tool_calls}, {response}")

        self.chat_store.add_message(self.chat_store_key, response.message)
        logger.info("Added LLM message to memory")
        
        if not tool_calls:
            logger.info("No tool calls detected, returning StopEvent")
            return StopEvent(
                result=json.dumps(
                    {
                        "response": response.message.content,
                    }
                )
            )

        for tool in tool_calls:
            if tool.tool_name in [
                t.metadata.get_name() for t in self.tools_needing_approval
            ]:
                await ctx.set("pending_tool", tool)
                await ctx.set("pending_tool_message", response.message)
                logger.info("Tool needs approval, returning InputRequiredEvent")

                # sys_msg = ChatMessage(
                #     role="system",
                #     content=f"Do you want to proceed with calling the tool {tool.tool_name}? (y/n)",
                # )
                # self.chat_store.add_message(self.chat_store_key, sys_msg)

                return InputRequiredEvent(
                    prefix="Waiting for human approval as Yes or No",
                    payload=f"Do you want to proceed with calling the tool {tool.tool_name}? (y/n)",
                )
        logger.info("Tool calls detected, returning ToolCallEvent")
        return ToolCallEvent(tool_calls=tool_calls)

    @step
    async def review_tool_calls(
        self, ctx: Context, ev: HumanResponseEvent
    ) -> InputEvent | ToolCallEvent | StopEvent:
        logger.info("Reviewing tool call step")
        pending_tool_call = await ctx.get("pending_tool")
        logger.info(f"Pending tool call: {pending_tool_call}")
        if ev.response.lower() == "y":
            # user_msg = ChatMessage(role="user", content=f"Yes, Approve")
            # self.chat_store.add_message(self.chat_store_key, user_msg)
            return ToolCallEvent(
                tool_calls=[pending_tool_call], stop_after_tool_call=True
            )
        else:
            additional_kwargs = {
                "tool_call_id": pending_tool_call.tool_id,
                "tool_name": pending_tool_call.tool_name,
                # "tool_kwargs": pending_tool_call.tool_kwargs
            }
            user_msg = ChatMessage(
                role="tool", content=f"No, Denied. Move on to next step)", additional_kwargs=additional_kwargs
            )
            self.chat_store.add_message(self.chat_store_key, user_msg)
            if ev.response.lower() == "n":
                return StopEvent(
                    result=json.dumps(
                        {
                            "response": "You've Denied the request for tool call. What am I supposed to do next?"
                        }
                    )
                )
            else:
                user_msg = ChatMessage(role="user", content=ev.response)
                self.chat_store.add_message(self.chat_store_key, user_msg)
                return InputEvent(input=self.chat_store.get_messages(self.chat_store_key))

    @step
    async def handle_tool_calls(self, ctx: Context, ev: ToolCallEvent) -> StopEvent:
        logger.info("Starting handle_tool_calls step")
        tool_calls = ev.tool_calls
        logger.info(f"Received tool calls: {tool_calls}")
        tools_by_name = {tool.metadata.get_name(): tool for tool in self.tools}

        tool_msgs = []
        logger.info("Starting tool execution loop")
        # call tools -- safely!
        for tool_call in tool_calls:
            tool = tools_by_name.get(tool_call.tool_name, None)
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
                if isinstance(tool, FunctionToolWithContext):
                    tool_output = await tool.acall(ctx, **tool_call.tool_kwargs)
                else:
                    tool_output = await tool.acall(**tool_call.tool_kwargs)

                self.tool_outputs.append(tool_output.content)
                self.sources.append(tool_output)
                logger.info(
                    f"Tool {tool.metadata.get_name()} output: {tool_output.content}"
                )
                # if ev.get("stop_after_tool_call", False):
                #     tool_msgs.append(await ctx.get("pending_tool_message"))
                #     logger.info(f"Tool Call, with approval {tool_msgs[0]}")
                # else:
                #     tool_msgs.append(tool_call)
                #     logger.info(f"Tool Call, without approval {tool_msgs[0]}")
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
            self.chat_store.add_message(self.chat_store_key, msg)
        chat_history = self.chat_store.get_messages(self.chat_store_key)
        logger.info(f"Retrieved chat history from memory, {chat_history}")
        logger.info("Completed handle_tool_calls step")
        return StopEvent(
            result=json.dumps(
                {
                    "response": tool_output.content,
                }
            )
        )