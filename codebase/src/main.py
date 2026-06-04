"""
FastAPI Server — MyVinpearl AI Booking Decision Assistant
- Serve HTML frontend tại /
- POST /api/chat → SSE stream (thinking + result)
- GET  /api/bookings → user bookings
- GET  /api/health
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env từ thư mục codebase/ (một cấp lên trên src/)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Validate OPENAI_API_KEY trước khi import agent
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY chưa được đặt trong .env")
    print("   Tạo file .env từ .env.example và điền API key vào")
    sys.exit(1)

# Add codebase/ root to sys.path so `src` package is importable
_ROOT = str(Path(__file__).parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.agent.graph import stream_agent_events, run_agent
from src.utils import mock_db


# ── FASTAPI APP ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="MyVinpearl AI Booking Assistant",
    description="AI Decision Assistant cho đặt phòng Vinpearl",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── SERVE FRONTEND ────────────────────────────────────────────────────────────

HTML_PATH = Path(__file__).parent.parent / "myvinpearl-ai-chatbot.html"


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve file HTML frontend."""
    if not HTML_PATH.exists():
        raise HTTPException(status_code=404, detail="Frontend HTML không tìm thấy")
    return HTML_PATH.read_text(encoding="utf-8")


# ── HEALTH CHECK ──────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "model_fast": os.getenv("OPENAI_MODEL_FAST", "gpt-4o-mini"),
        "model_smart": os.getenv("OPENAI_MODEL_SMART", "gpt-4o-mini"),
    }


# ── BOOKINGS ENDPOINT ─────────────────────────────────────────────────────────

@app.get("/api/bookings")
async def get_bookings(user_id: str = "demo_user"):
    """Trả về danh sách booking của user."""
    bookings = mock_db.get_user_bookings(user_id)
    return {"bookings": bookings}


# ── CHAT ENDPOINT (SSE STREAMING) ────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    user_id: str = "demo_user"
    session_id: Optional[str] = None
    context: Optional[dict] = None     # {"booking_ref": "..."} etc.
    history: Optional[list] = None     # [{"role":"user","content":"..."},...] for conversation history


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Main agent entry — trả về Server-Sent Events stream.
    Event types:
      thinking_start  → bắt đầu xử lý
      thinking_item   → {text, ok} — checklist item
      thinking_progress → {value: 0–100} — progress bar
      result          → {intent, ui_state, result_data, entities, llm_response, thinking_steps}
                         ui_state values: show_destinations | show_change_booking |
                                          show_cancel_booking | show_message | show_error
      error           → {message}
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message không được để trống")

    async def event_generator():
        try:
            async for chunk in stream_agent_events(
                message=request.message,
                history=request.history,
                user_id=request.user_id,
                context=request.context,
            ):
                yield chunk
        except Exception as e:
            error_payload = json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False)
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",    # disable nginx buffering
        },
    )


# ── BOOKING ENDPOINT ─────────────────────────────────────────────────────────

class BookingRequest(BaseModel):
    hotel_id: str
    room_id: str
    checkin: str = "2026-06-05"
    checkout: str = "2026-06-06"
    guests: int = 2
    user_name: str = ""
    email: str = ""


@app.post("/api/book")
async def create_booking(req: BookingRequest):
    """
    Mock booking confirmation.
    In production this would write to a database and send a confirmation email.
    """
    import random, string
    suffix = ''.join(random.choices(string.digits, k=4))
    ref = f"VNP-2026-{suffix}"
    return {
        "success": True,
        "booking_ref": ref,
        "hotel_id": req.hotel_id,
        "room_id": req.room_id,
        "checkin": req.checkin,
        "checkout": req.checkout,
        "guests": req.guests,
        "user_name": req.user_name,
        "email": req.email,
        "message": f"Đặt phòng thành công! Mã booking: {ref}. Email xác nhận đã gửi tới {req.email}.",
    }


# ── POLICY ENDPOINT ──────────────────────────────────────────────────────────

@app.get("/api/policy")
async def get_policy():
    """Trả về nội dung POLICY.md đã được dedup."""
    try:
        from src.utils.policy import POLICY_CONTENT
        return {"content": POLICY_CONTENT, "chars": len(POLICY_CONTENT)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── RESORT/ROOM DATA ENDPOINTS ────────────────────────────────────────────────

@app.get("/api/destinations")
async def get_destinations():
    return {"destinations": list(mock_db.DESTINATIONS.values())}


@app.get("/api/resorts/{destination_id}")
async def get_resorts(destination_id: str):
    resorts = mock_db.get_resorts_by_destination(destination_id)
    if not resorts:
        raise HTTPException(status_code=404, detail=f"Không có resort ở {destination_id}")
    return {"resorts": resorts}


@app.get("/api/availability/{hotel_id}")
async def get_hotel_availability(hotel_id: str, start: str = "", nights: int = 21):
    """Trả về availability calendar cho hotel trong N ngày từ start (YYYY-MM-DD)."""
    import datetime
    if not start:
        start = datetime.date.today().isoformat()
    data = mock_db.get_hotel_availability(hotel_id, start, nights)
    return {"hotel_id": hotel_id, "availability": data}


@app.get("/api/rooms/{resort_id}")
async def get_rooms(resort_id: str):
    rooms = mock_db.get_rooms_by_resort(resort_id)
    return {"rooms": rooms}


@app.get("/api/availability")
async def get_availability(resort_id: str, room_id: str, anchor_date: str = "2024-06-20"):
    dates = mock_db.get_availability_grid(resort_id, room_id, anchor_date)
    return {"dates": dates}


# ── ENTRYPOINT ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    print(f"""
╔══════════════════════════════════════════════════════╗
║         VinpearlAI — Backend Server                  ║
╠══════════════════════════════════════════════════════╣
║  Local:      http://localhost:{port}                   ║
║  Network:    http://{host}:{port}                  ║
║                                                      ║
║  Frontend:   http://localhost:{port}/                  ║
║  API docs:   http://localhost:{port}/docs              ║
║  Health:     http://localhost:{port}/api/health        ║
╚══════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=[str(Path(__file__).parent)],
        log_level="info",
    )
