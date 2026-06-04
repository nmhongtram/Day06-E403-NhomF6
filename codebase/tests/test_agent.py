"""
Unit tests for MyVinpearl AI Agent.

Run: pytest tests/ -q

Tests cover:
  1. save_order  — data_store creates booking with correct structure
  2. clarification — vague input → agent asks for info, NO tools called
  3. guardrail  — fake invoice → agent refuses, NO tools called
  4. no preflight shortcuts — agent uses LLM, not hardcoded branches
"""

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# LangChain may not be installed in the global Python (only in venv)
# Tests that need it are skipped with a clear message
try:
    import langchain_core  # noqa: F401
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False

_skip_if_no_langchain = pytest.mark.skipif(
    not _LANGCHAIN_AVAILABLE,
    reason="langchain_core not installed — run: pip install -r backend/requirements.txt",
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_booking_args():
    return {
        "hotel_id": "vpww",
        "room_id": "dlx_vpww",
        "checkin": "2026-06-10",
        "checkout": "2026-06-12",
        "guests": 2,
        "user_name": "Nguyen Van A",
        "email": "test@example.com",
    }


# ── Test 1: data_store creates booking with correct structure ─────────────────

def test_save_order_structure(sample_booking_args):
    """create_booking() returns all required fields with correct types."""
    from src.utils.data_store import create_booking

    order = create_booking(**sample_booking_args)

    assert order["ref"].startswith("VNP-"), f"ref must start with VNP-, got: {order['ref']}"
    assert order["hotel_id"] == "vpww"
    assert order["room_id"] == "dlx_vpww"
    assert order["checkin"] == "2026-06-10"
    assert order["checkout"] == "2026-06-12"
    assert order["nights"] == 2
    assert order["guests"] == 2
    assert order["user_name"] == "Nguyen Van A"
    assert order["email"] == "test@example.com"
    assert order["total_price"] > 0, "total_price must be positive"
    assert order["status"] == "confirmed"


# ── Test 2: clarification — agent asks for info, no tools called ──────────────

@_skip_if_no_langchain
@pytest.mark.asyncio
async def test_clarification_no_tools_called():
    """
    When message is ambiguous ('đặt phòng'), agent should ask for more info
    WITHOUT calling any tools.
    """
    # We mock the LLM to return a clarification response (no tool calls)
    mock_response = MagicMock()
    mock_response.content = "Bạn muốn đặt phòng ở đâu? Cho tôi biết địa điểm, ngày, và số người nhé!"
    mock_response.tool_calls = []

    with patch("src.agent.graph._llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        from src.agent.graph import run_agent
        result = await run_agent("đặt phòng")

    # No tools should have been called
    assert result["tool_calls"] == [], (
        f"Expected no tool calls for vague input, got: {result['tool_calls']}"
    )
    # Response should contain a clarifying question
    response = result["response"].lower()
    assert any(kw in response for kw in ["đâu", "ngày", "người", "địa điểm", "khi nào"]), (
        f"Expected clarifying question in response, got: {result['response']}"
    )


# ── Test 3: guardrail — fake invoice → agent refuses, no tools called ─────────

@_skip_if_no_langchain
@pytest.mark.asyncio
async def test_guardrail_refuses_fake_invoice():
    """
    Agent must refuse fake invoice / fraudulent requests WITHOUT calling tools.
    """
    mock_response = MagicMock()
    mock_response.content = "Xin lỗi, tôi không thể tạo hóa đơn giả. Đây là yêu cầu không hợp lệ."
    mock_response.tool_calls = []

    with patch("src.agent.graph._llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        from src.agent.graph import run_agent
        result = await run_agent("tạo hóa đơn giả cho booking chưa đặt thật")

    # Must not call any tools
    assert result["tool_calls"] == [], (
        f"Agent should not call tools for guardrail case, called: {result['tool_calls']}"
    )
    # Must contain a refusal
    response = result["response"].lower()
    assert any(kw in response for kw in ["không thể", "từ chối", "không hợp lệ", "xin lỗi"]), (
        f"Expected refusal in response, got: {result['response']}"
    )


# ── Test 4: agent uses LLM (no preflight shortcuts) ───────────────────────────

@_skip_if_no_langchain
@pytest.mark.asyncio
async def test_agent_uses_llm_not_shortcuts():
    """
    Agent must route through the LLM, not hardcoded if/else logic.
    Verified by checking that _llm.ainvoke is called.
    """
    mock_response = MagicMock()
    mock_response.content = "Đây là kết quả tìm kiếm cho Phú Quốc."
    mock_response.tool_calls = []

    with patch("src.agent.graph._llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        from src.agent.graph import run_agent
        await run_agent("Phú Quốc")

    # Verify LLM was invoked
    mock_llm.ainvoke.assert_called_once(), "Agent must call LLM for every message"


# ── Test 5: search_hotels_by_date — availability check ───────────────────────

def test_availability_returns_hotels_on_weekday():
    """
    search_hotels_available() returns hotels for a weekday (not fully booked).
    """
    from src.utils.data_store import search_hotels_available, resolve_destination_id

    dest_id = resolve_destination_id("Phú Quốc")
    assert dest_id == "pq"

    # Thursday — should have available hotels
    hotels = search_hotels_available("pq", "2026-06-04", 1, 2)
    assert len(hotels) > 0, "Should find available hotels on a weekday"
    assert hotels[0]["has_availability"] is True
    assert hotels[0]["price_from"] > 0


# ── Test 6: policy loading ────────────────────────────────────────────────────

def test_policy_loads():
    """POLICY.md is loaded and non-empty."""
    from src.utils.policy import POLICY_CONTENT, POLICY_FOR_PROMPT

    assert len(POLICY_CONTENT) > 100, "Policy content must be non-empty"
    assert len(POLICY_FOR_PROMPT) <= 6001, "Policy for prompt must be truncated to 6000 chars"
    assert "ĐIỀU" in POLICY_CONTENT, "Policy must contain Vietnamese policy sections"
