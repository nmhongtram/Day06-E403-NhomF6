"""
MyVinpearl AI Booking Agent — LangGraph ReAct implementation.

Architecture:
  START → agent_node ⇄ tool_node → END

Why ReAct over classify-route:
  - Conversation history via add_messages (fixes multi-turn context)
  - LLM decides tool sequence naturally (no misclassification cascade)
  - Single coherent system prompt (not 7 fragmented ones)
  - Multi-step reasoning per request (e.g. search → details → save)

Tool calling order (happy path):
  search_hotels_by_date → get_hotel_rooms → save_booking
  check_booking → calculate_refund         (cancel flow)
  check_booking → check_available_dates    (change flow)
"""

import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# Ensure hackathon/ root is on sys.path
_ROOT = str(Path(__file__).parent.parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.core.llm import get_llm
from src.utils.data_store import (
    compute_refund,
    create_booking,
    get_available_change_dates,
    get_booking,
    get_hotel_rooms as _get_hotel_rooms,
    get_hotels_for_destination,
    parse_checkin_date,
    resolve_destination_id,
    search_destinations,
    search_hotels_available,
)
from src.utils.policy import POLICY_FOR_PROMPT


# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────

_SYSTEM_TEMPLATE = """Bạn là Virtual Agent của MyVinpearl — trợ lý đặt phòng khách sạn thông minh.

**Tính cách:** Thân thiện, chính xác, ngắn gọn. Trả lời bằng tiếng Việt.

**Luồng đặt phòng (khi user có ngày cụ thể):**
  1. search_hotels_by_date → hiển thị khách sạn còn trống
  2. get_hotel_rooms → xem phòng tại khách sạn đã chọn
  3. save_booking → xác nhận đặt phòng

**Luồng đặt phòng (khi chưa có ngày):**
  1. search_hotels → gợi ý điểm đến phù hợp
  2. get_hotel_rooms → xem phòng khi user đã chọn điểm
  3. save_booking → xác nhận

**Luồng hủy booking:**
  1. calculate_refund → tính phí hủy và số tiền hoàn

**Luồng đổi ngày:**
  1. check_booking → lấy thông tin booking
  2. check_available_dates → xem ngày trống

**Quy tắc quan trọng:**
- Nếu thiếu thông tin để đặt phòng → hỏi MỘT câu cụ thể, KHÔNG gọi tool
- Hiển thị giá và tóm tắt rõ ràng trước khi save_booking
- Không bịa đặt thông tin booking hoặc giá
- Từ chối yêu cầu tạo hóa đơn giả, booking không có thật
- Sau khi gọi tool, diễn giải kết quả bằng ngôn ngữ tự nhiên thân thiện

**ĐỊNH DẠNG CÂU TRẢ LỜI (bắt buộc):**
- Sau search_hotels / search_hotels_by_date / get_hotel_rooms → viết TỐI ĐA 1 câu mở đầu (≤15 từ)
  ✓ ĐÚNG: "Còn 3 khách sạn trống ngày 7/6! 🏖"
  ✗ SAI: liệt kê chi tiết từng khách sạn với giá/hình ảnh/rating
  Lý do: frontend hiển thị card tự động — text chỉ là lời dẫn
- Sau calculate_refund: 1-2 câu tóm tắt số tiền hoàn
- Câu hỏi QA/chính sách: 2-4 câu đầy đủ
- Hỏi thêm thông tin: 1 câu ngắn + 2-3 gợi ý cụ thể

Hôm nay: {today}

**Chính sách Vinpearl (dùng để trả lời câu hỏi trực tiếp):**
{policy}
"""


def _build_system() -> SystemMessage:
    today = date.today().strftime("%d/%m/%Y")
    content = _SYSTEM_TEMPLATE.format(today=today, policy=POLICY_FOR_PROMPT[:2000])
    return SystemMessage(content=content)


# ── TOOLS ─────────────────────────────────────────────────────────────────────

@tool
def search_hotels(
    destination: str = None,
    vibe: str = None,
    trip_type: str = None,
    guest_count: int = 2,
    budget: int = None,
    nights: int = None,
) -> str:
    """
    Tìm và xếp hạng khách sạn/resort Vinpearl theo sở thích — dùng khi CHƯA có ngày cụ thể.

    Args:
        destination: Tên địa điểm (Phú Quốc, Nha Trang, Đà Nẵng, Hạ Long, Huế)
        vibe: beach | city | nature | culture
        trip_type: family | couple | solo | group
        guest_count: Số người
        budget: Ngân sách tổng (VND)
        nights: Số đêm dự kiến

    Returns:
        JSON: top 3 điểm đến phù hợp nhất với điểm match và lý do
    """
    entities = {k: v for k, v in {
        "destination": destination, "vibe": vibe, "trip_type": trip_type,
        "guest_count": guest_count, "budget": budget, "nights": nights,
    }.items() if v is not None}

    if destination:
        dest_id = resolve_destination_id(destination)
        if dest_id:
            hotels = get_hotels_for_destination(dest_id, entities)
            return json.dumps({
                "type": "hotels",
                "destination": destination,
                "destination_id": dest_id,
                "hotels": [{
                    "id": h["id"], "name": h["name"], "match_score": h["match_score"],
                    "rating": h.get("rating"), "price_from": h.get("price_from"),
                    "image": h.get("image"), "reasons": h.get("reasons", [])[:3],
                } for h in hotels],
            }, ensure_ascii=False)
        return json.dumps({"error": f"Vinpearl chưa có dịch vụ tại '{destination}'. Các điểm có: Phú Quốc, Nha Trang, Đà Nẵng, Hạ Long, Huế."}, ensure_ascii=False)

    destinations = search_destinations(entities)
    return json.dumps({
        "type": "destinations",
        "destinations": [{
            "id": d["id"], "name": d["name"], "match_score": d["match_score"],
            "rating": d.get("rating"), "image": d.get("image"),
            "reasons": d.get("reasons", [])[:3], "description": d.get("description", ""),
        } for d in destinations],
    }, ensure_ascii=False)


@tool
def search_hotels_by_date(
    destination: str,
    checkin_date: str,
    nights: int = 1,
    guest_count: int = 2,
    vibe: str = None,
    trip_type: str = None,
) -> str:
    """
    Tìm khách sạn còn trống cho ngày cụ thể — dùng KHI USER NÓI NGÀY (5/6, cuối tuần, ...).

    Args:
        destination: Tên địa điểm (Phú Quốc, Nha Trang, Đà Nẵng, Hạ Long, Huế)
        checkin_date: Ngày check-in — YYYY-MM-DD, D/M, "cuối tuần này", "tuần tới"
        nights: Số đêm (mặc định 1)
        guest_count: Số người lớn
        vibe: beach | city | nature | culture
        trip_type: family | couple | solo | group

    Returns:
        JSON: danh sách khách sạn còn trống với giá và số phòng có sẵn
    """
    parsed = parse_checkin_date(checkin_date)
    if not parsed:
        return json.dumps({"error": f"Không xác định được ngày từ '{checkin_date}'."}, ensure_ascii=False)

    dest_id = resolve_destination_id(destination)
    if not dest_id:
        return json.dumps({"error": f"Vinpearl chưa có dịch vụ tại '{destination}'."}, ensure_ascii=False)

    from datetime import date as _date, timedelta as _td
    try:
        checkout = (_date.fromisoformat(parsed) + _td(days=nights)).isoformat()
    except Exception:
        checkout = parsed

    hotels = search_hotels_available(dest_id, parsed, nights, guest_count)
    if not hotels:
        return json.dumps({
            "available": False,
            "destination": destination,
            "checkin": parsed,
            "nights": nights,
            "message": f"Không còn phòng trống tại {destination} ngày {parsed} cho {guest_count} người.",
        }, ensure_ascii=False)

    return json.dumps({
        "available": True,
        "type": "hotels_by_date",
        "destination": destination,
        "destination_id": dest_id,
        "checkin": parsed,
        "checkout": checkout,
        "nights": nights,
        "hotels": [{
            "id": h["id"], "name": h["name"],
            "available_rooms_count": h.get("available_rooms_count", 0),
            "price_from": h.get("price_from"), "price": h.get("price_from"),
            "rating": h.get("rating"), "image": h.get("image"),
            "has_availability": True, "checkin": parsed, "checkout": checkout,
        } for h in hotels],
        "count": len(hotels),
    }, ensure_ascii=False)


@tool
def get_hotel_rooms(
    hotel_id: str,
    checkin_date: str = None,
    guest_count: int = 2,
) -> str:
    """
    Lấy danh sách các loại phòng của một khách sạn cụ thể.

    Args:
        hotel_id: ID khách sạn (từ kết quả search trước đó)
        checkin_date: Ngày check-in để kiểm tra giá (tùy chọn)
        guest_count: Số người để lọc phòng phù hợp

    Returns:
        JSON: danh sách phòng với giá, sức chứa, tiện ích
    """
    entities = {"guest_count": guest_count}
    if checkin_date:
        parsed = parse_checkin_date(checkin_date)
        if parsed:
            entities["checkin_date"] = parsed

    rooms = _get_hotel_rooms(hotel_id, entities)
    if not rooms:
        return json.dumps({"error": f"Không tìm thấy phòng nào tại khách sạn '{hotel_id}'."}, ensure_ascii=False)

    return json.dumps({
        "type": "rooms",
        "hotel_id": hotel_id,
        "rooms": [{
            "id": r["id"], "name": r["name"],
            "capacity": r.get("capacity", 2),
            "price": r.get("price_per_night", r.get("price", 0)),
            "price_per_night": r.get("price_per_night", r.get("price", 0)),
            "image": r.get("image"), "match_score": r.get("match_score"),
            "ai_pick": r.get("ai_pick", False),
            "reasons": r.get("reasons", [])[:3],
            "attributes": r.get("attributes", []),
        } for r in rooms],
    }, ensure_ascii=False)


@tool
def check_booking(user_id: str = "demo_user", booking_ref: str = None) -> str:
    """
    Lấy thông tin booking hiện tại của khách hàng.

    Args:
        user_id: ID người dùng (mặc định: demo_user)
        booking_ref: Mã booking (VNP-XXXX-XXXX). Nếu không có → lấy booking mới nhất.

    Returns:
        JSON: thông tin chi tiết booking
    """
    booking = get_booking(user_id, booking_ref)
    if not booking:
        return json.dumps({"error": "Không tìm thấy booking nào. Kiểm tra lại mã booking hoặc liên hệ CSKH 1800 1234."}, ensure_ascii=False)
    return json.dumps({
        "type": "booking",
        "ref": booking["ref"],
        "resort_name": booking.get("resort_name", booking.get("hotel_name", "")),
        "destination": booking.get("destination", ""),
        "room_type": booking.get("room_type", booking.get("room_name", "")),
        "checkin": booking["checkin"],
        "checkout": booking["checkout"],
        "nights": booking["nights"],
        "guests": booking["guests"],
        "total_paid": booking["total_paid"],
        "status": booking["status"],
    }, ensure_ascii=False)


@tool
def calculate_refund(user_id: str = "demo_user", booking_ref: str = None) -> str:
    """
    Tính toán phí hủy và số tiền hoàn lại theo chính sách Vinpearl.

    Args:
        user_id: ID người dùng
        booking_ref: Mã booking (VNP-XXXX-XXXX)

    Returns:
        JSON: số ngày đến check-in, % phí hủy, số tiền hoàn, thời gian hoàn
    """
    data = compute_refund(user_id, booking_ref)
    if not data:
        return json.dumps({"error": "Không tìm thấy booking để tính hoàn tiền. Liên hệ CSKH 1800 1234."}, ensure_ascii=False)
    b = data["booking"]
    r = data["refund"]
    return json.dumps({
        "type": "refund",
        "booking_ref": b["ref"],
        "resort_name": b.get("resort_name", ""),
        "checkin": b["checkin"],
        "total_paid": b["total_paid"],
        "days_until_checkin": r["days_until_checkin"],
        "fee_pct": r["fee_pct"],
        "fee_amount": r["fee_amount"],
        "refund_amount": r["refund_amount"],
        "tier_label": r["tier_label"],
        "refund_timeline": r["refund_timeline"],
        "policy_tiers": data["policy_tiers"],
    }, ensure_ascii=False)


@tool
def check_available_dates(user_id: str = "demo_user", booking_ref: str = None) -> str:
    """
    Kiểm tra các ngày có thể đổi check-in và phí đổi ngày.

    Args:
        user_id: ID người dùng
        booking_ref: Mã booking

    Returns:
        JSON: danh sách ngày trống ±7 ngày, chính sách đổi ngày
    """
    data = get_available_change_dates(user_id, booking_ref)
    if not data:
        return json.dumps({"error": "Không tìm thấy booking. Liên hệ CSKH 1800 1234."}, ensure_ascii=False)
    policy = data["change_policy"]
    available = [d for d in data["available_dates"] if d["available"] and not d.get("is_current")]
    return json.dumps({
        "type": "available_dates",
        "booking_ref": data["booking"]["ref"],
        "current_checkin": data["booking"]["checkin"],
        "available_dates": available[:6],
        "change_policy": {
            "free_before_days": policy["free_change_before_days"],
            "fee": policy["change_fee"],
            "max_changes": policy["max_changes"],
        },
    }, ensure_ascii=False)


@tool
def save_booking(
    hotel_id: str,
    room_id: str,
    checkin_date: str,
    checkout_date: str,
    guests: int,
    user_name: str,
    email: str,
) -> str:
    """
    Xác nhận và lưu đặt phòng mới. Gọi tool này CHỈ KHI user đã xác nhận tất cả thông tin.

    Args:
        hotel_id: ID khách sạn (từ kết quả search)
        room_id: ID phòng (từ get_hotel_rooms)
        checkin_date: Ngày check-in YYYY-MM-DD
        checkout_date: Ngày check-out YYYY-MM-DD
        guests: Số người lớn
        user_name: Tên đầy đủ khách
        email: Email nhận xác nhận

    Returns:
        JSON: mã booking, tên khách sạn, phòng, tổng tiền
    """
    order = create_booking(hotel_id, room_id, checkin_date, checkout_date, guests, user_name, email)
    return json.dumps({
        "type": "booking_confirmed",
        "ref": order["ref"],
        "hotel_name": order["hotel_name"],
        "room_name": order["room_name"],
        "checkin": order["checkin"],
        "checkout": order["checkout"],
        "nights": order["nights"],
        "guests": order["guests"],
        "total_price": order["total_price"],
        "email": order["email"],
        "message": f"Đặt phòng thành công! Mã: {order['ref']}. Email xác nhận sẽ gửi đến {order['email']}.",
    }, ensure_ascii=False)


# ── LANGGRAPH REACT GRAPH ─────────────────────────────────────────────────────

TOOLS = [
    search_hotels,
    search_hotels_by_date,
    get_hotel_rooms,
    check_booking,
    calculate_refund,
    check_available_dates,
    save_booking,
]


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


_llm = get_llm().bind_tools(TOOLS)
_tool_node = ToolNode(TOOLS)


async def _agent_node(state: State) -> dict:
    """LLM call — appends one AIMessage (possibly with tool_calls)."""
    response = await _llm.ainvoke([_build_system()] + state["messages"])
    return {"messages": [response]}


def _should_continue(state: State) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "__end__"


_graph_builder = StateGraph(State)
_graph_builder.add_node("agent", _agent_node)
_graph_builder.add_node("tools", _tool_node)
_graph_builder.add_edge(START, "agent")
_graph_builder.add_conditional_edges("agent", _should_continue, {"tools": "tools", "__end__": END})
_graph_builder.add_edge("tools", "agent")

agent_graph = _graph_builder.compile()


# ── UI STATE MAPPING ──────────────────────────────────────────────────────────

def _extract_tool_log(messages: list[BaseMessage]) -> list[dict]:
    """Extract {name, args, result} for each tool call/result pair."""
    calls: dict[str, dict] = {}
    results: dict[str, str] = {}

    for msg in messages:
        if isinstance(msg, AIMessage):
            for tc in (msg.tool_calls or []):
                calls[tc["id"]] = {"name": tc["name"], "args": tc.get("args", {})}
        elif isinstance(msg, ToolMessage):
            results[msg.tool_call_id] = msg.content

    return [
        {"name": calls[k]["name"], "args": calls[k]["args"], "result": results.get(k, "")}
        for k in calls
    ]


def _tool_result_data(tool_name: str, result_json: str) -> dict:
    try:
        return json.loads(result_json)
    except Exception:
        return {}


def _infer_ui_state(tool_log: list[dict]) -> tuple[str, dict]:
    """Map last meaningful tool call → (ui_state, result_data)."""
    if not tool_log:
        return "show_message", {}

    # Priority order: save first, then date-search, then general search, etc.
    tool_priority = [
        "save_booking", "search_hotels_by_date", "search_hotels",
        "get_hotel_rooms", "calculate_refund", "check_available_dates", "check_booking",
    ]
    ui_map = {
        "save_booking":           "show_booking_success",
        "search_hotels_by_date":  "show_hotels",
        "search_hotels":          "show_destinations",  # may also be show_hotels if dest known
        "get_hotel_rooms":        "show_rooms",
        "calculate_refund":       "show_cancel_booking",
        "check_available_dates":  "show_change_booking",
        "check_booking":          "show_message",
    }

    tools_called = {t["name"] for t in tool_log}
    for priority_tool in tool_priority:
        if priority_tool in tools_called:
            entry = next(t for t in reversed(tool_log) if t["name"] == priority_tool)
            data = _tool_result_data(priority_tool, entry["result"])
            ui = ui_map[priority_tool]
            # Refine: search_hotels returning hotels (not destinations) → show_hotels
            if priority_tool == "search_hotels" and data.get("type") == "hotels":
                ui = "show_hotels"
            return ui, data

    return "show_message", {}


# ── PUBLIC API ────────────────────────────────────────────────────────────────

def _build_messages(history: list[dict] | None) -> list[BaseMessage]:
    """Convert [{role:'user'|'assistant', content:'...'}] → LangChain messages."""
    if not history:
        return []
    result = []
    for h in history[-10:]:  # keep last 5 exchanges
        role = h.get("role", "")
        content = h.get("content", "")
        if role == "user":
            result.append(HumanMessage(content=content))
        elif role in ("assistant", "bot"):
            result.append(AIMessage(content=content))
    return result


async def run_agent(
    message: str,
    history: list[dict] | None = None,
    user_id: str = "demo_user",
) -> dict:
    """
    Non-streaming entry point.

    Args:
        message: User input text
        history: Previous conversation [{"role":"user","content":"..."},...]
        user_id: For booking lookup

    Returns:
        {"response": str, "ui_state": str, "result_data": dict, "tool_calls": list}
    """
    messages = _build_messages(history) + [HumanMessage(content=message)]
    result = await agent_graph.ainvoke({"messages": messages})

    all_messages = result["messages"]
    last_ai = next((m for m in reversed(all_messages) if isinstance(m, AIMessage) and not m.tool_calls), None)
    response_text = last_ai.content if last_ai else ""

    tool_log = _extract_tool_log(all_messages)
    ui_state, result_data = _infer_ui_state(tool_log)
    response_text = _shorten_to_intro(response_text) if ui_state in _CARD_STATES else _strip_markdown(response_text)
    result_data["llm_message"] = response_text

    return {
        "response": response_text,
        "ui_state": ui_state,
        "result_data": result_data,
        "tool_calls": tool_log,
    }


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


_TOOL_LABELS = {
    "search_hotels":          "🔍 Đang tìm kiếm khách sạn...",
    "search_hotels_by_date":  "📅 Đang kiểm tra phòng trống...",
    "get_hotel_rooms":        "🛏 Đang xem danh sách phòng...",
    "check_booking":          "📋 Đang lấy thông tin booking...",
    "calculate_refund":       "💰 Đang tính toán hoàn tiền...",
    "check_available_dates":  "📅 Đang kiểm tra ngày trống...",
    "save_booking":           "✓ Đang xác nhận đặt phòng...",
}

# States where LLM text is just an intro — cards render the actual data
_CARD_STATES = {"show_hotels", "show_destinations", "show_rooms", "show_cancel_booking", "show_change_booking", "show_booking_success"}


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting, list items, and image links."""
    if not text:
        return text
    lines = text.split("\n")
    cleaned: list[str] = []
    for line in lines:
        t = line.strip()
        if not t:
            continue
        # Skip list items, numbered items, standalone image markdown
        if re.match(r"^[-*•]\s", t) or re.match(r"^\d+\.\s", t) or t.startswith("!["):
            continue
        # Strip inline markdown syntax
        t = re.sub(r"!\[.*?\]\(.*?\)", "", t)     # inline images
        t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)    # **bold**
        t = re.sub(r"\*(.+?)\*", r"\1", t)         # *italic*
        t = re.sub(r"`(.+?)`", r"\1", t)           # `code`
        t = re.sub(r"\[(.+?)\]\(.*?\)", r"\1", t)  # [link](url)
        t = re.sub(r"^#{1,6}\s+", "", t)           # headers
        t = t.strip()
        if t:
            cleaned.append(t)
    return "\n".join(cleaned).strip()


def _shorten_to_intro(text: str) -> str:
    """For card-showing responses: return only the first prose sentence."""
    if not text:
        return text
    clean = _strip_markdown(text)
    if not clean:
        return ""
    # Keep just the first line (intro sentence before any list)
    return clean.split("\n")[0][:160]


async def stream_agent_events(
    message: str,
    history: list[dict] | None = None,
    user_id: str = "demo_user",
    context: dict | None = None,
):
    """
    SSE generator — single ainvoke run, then yield thinking items + result.

    Runs the graph ONCE (not twice) for efficiency.
    Yields server-sent events compatible with the existing frontend format.
    """
    import asyncio

    # Inject saved booking_ref into message context if provided
    user_message = message
    if context and context.get("booking_ref"):
        user_message = f"[Mã booking của bạn: {context['booking_ref']}] {message}"

    yield _sse({"type": "thinking_start"})
    await asyncio.sleep(0.03)

    all_messages = _build_messages(history) + [HumanMessage(content=user_message)]

    try:
        # Single graph invocation — wrap so exceptions become SSE error events
        final_state = await agent_graph.ainvoke({"messages": all_messages})
    except Exception as exc:
        yield _sse({"type": "error", "message": str(exc)})
        return

    all_msgs = final_state.get("messages", [])

    # Emit thinking items for each tool that was called
    tool_log = _extract_tool_log(all_msgs)
    for t in tool_log:
        yield _sse({"type": "thinking_item", "text": _TOOL_LABELS.get(t["name"], f"🔧 {t['name']}..."), "ok": True})
        await asyncio.sleep(0.12)

    yield _sse({"type": "thinking_progress", "value": 100})
    await asyncio.sleep(0.05)

    # Extract final text response (last AIMessage without tool_calls)
    last_ai = next((m for m in reversed(all_msgs) if isinstance(m, AIMessage) and not m.tool_calls), None)
    response_text = (last_ai.content or "").strip() if last_ai else ""

    ui_state, result_data = _infer_ui_state(tool_log)

    # Card states: keep only the first intro sentence
    if ui_state in _CARD_STATES:
        response_text = _shorten_to_intro(response_text)
    else:
        # All other states: strip markdown formatting
        response_text = _strip_markdown(response_text)

    result_data["llm_message"] = response_text

    yield _sse({
        "type": "result",
        "intent": _infer_intent(tool_log),
        "ui_state": ui_state,
        "result_data": result_data,
        "llm_response": response_text,
        "tool_calls": tool_log,
        "entities": {},
        "thinking_steps": [{"text": t["name"], "ok": True} for t in tool_log],
    })


def _infer_intent(tool_log: list[dict]) -> str:
    tools_called = {t["name"] for t in tool_log}
    if "save_booking" in tools_called:
        return "book"
    if "search_hotels_by_date" in tools_called or "search_hotels" in tools_called:
        return "search"
    if "calculate_refund" in tools_called:
        return "cancel"
    if "check_available_dates" in tools_called:
        return "change"
    return "qa"
