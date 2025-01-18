from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

from llama_index.core.llms import ChatMessage
from llama_index.core.tools import ToolSelection, ToolOutput
from llama_index.core.workflow import Event


class InputData(BaseModel): 
    query: str
    customer_data: Optional[Dict[str, Any]]

class RequestBody(BaseModel):
    user_id: str
    session_id: str
    input: InputData


class InputEvent(Event):
    input: list[ChatMessage]


class ToolCallEvent(Event):
    tool_calls: list[ToolSelection]


class FunctionOutputEvent(Event):
    output: ToolOutput