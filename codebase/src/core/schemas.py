"""Pydantic schemas for I/O between agent layers."""

from typing import Annotated, Optional, TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """LangGraph state: messages accumulate via add_messages reducer."""
    messages: Annotated[list[BaseMessage], add_messages]


class BookingOrder(BaseModel):
    ref: str
    hotel_id: str
    hotel_name: str
    room_id: str
    room_name: str
    checkin: str
    checkout: str
    nights: int
    guests: int
    total_price: int
    user_name: str
    email: str


class SearchResult(BaseModel):
    destinations: list[dict] = Field(default_factory=list)
    hotels: list[dict] = Field(default_factory=list)
    rooms: list[dict] = Field(default_factory=list)


class AgentResponse(BaseModel):
    """Final structured response from run_agent()."""
    response: str                       # natural-language text for chat bubble
    ui_state: str = "show_message"      # what the frontend should render
    result_data: dict = Field(default_factory=dict)
    tool_calls: list[dict] = Field(default_factory=list)   # [{name, args, result}, ...]
