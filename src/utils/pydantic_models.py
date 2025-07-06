from typing import Optional, Any, Dict, TypedDict
from pydantic import BaseModel

from llama_index.core.tools import ToolSelection, ToolOutput
from llama_index.core.workflow import Event
from llama_index.core.llms import ChatMessage


class InputData(BaseModel):
    query: str
    customer_data: Optional[Dict[str, Any]] = None

class RequestBody(BaseModel):
    user_id: str
    input: InputData
    session_id: Optional[str] = None


class InputEvent(Event):
    input: list[ChatMessage]


class ToolCallEvent(Event):
    tool_calls: list[ToolSelection]


class FunctionOutputEvent(Event):
    output: ToolOutput