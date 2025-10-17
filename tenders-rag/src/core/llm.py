import dataclasses
import json
from typing import Any

import openai

from ..tools import base
from . import config

client = openai.OpenAI(api_key=config.OPENAI_API_KEY)


@dataclasses.dataclass
class ToolCall:
    id: str
    name: str
    args: dict

@dataclasses.dataclass
class ChatResponse:
    message: str | None = None
    tool_calls: list[ToolCall] | None = None
    original_tool_calls: Any | None = None

def chat(history, tools: list[base.Tool]) -> ChatResponse:

    response = client.chat.completions.create(
        model=config.MODEL,
        messages=history,
        tools=[tool.schema() for tool in tools]
    )

    message = response.choices[0].message

    output = ChatResponse()  # messages = None, tool_calls = None

    if message.content:
        output.message = message.content

    elif message.tool_calls:
        output.original_tool_calls = message.tool_calls
        
        output.tool_calls = []
        for tool_call in message.tool_calls:
            output.tool_calls.append(
                ToolCall(
                    id=tool_call.id,
                    name=tool_call.function.name,  # type: ignore
                    args=json.loads(tool_call.function.arguments),  # type: ignore
                )
            )
    
    else:
        # Explode
        raise RuntimeError("No message and no tool calls? What???")

    return output
