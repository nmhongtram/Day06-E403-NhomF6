# MyVinpearl AI Booking Assistant — Setup Guide

## Yêu cầu

- Python 3.10+
- OpenAI API key ([lấy tại đây](https://platform.openai.com/api-keys))

---

## Cài đặt nhanh (Windows)

### Bước 1 — Tạo file .env

```bat
cd hackathon
copy .env.example .env
```

Mở `.env`, điền API key:
```
OPENAI_API_KEY=sk-proj-xxx...
```

### Bước 2 — Chạy server

Double-click `start.bat` hoặc:

```bat
cd hackathon
start.bat
```

Server sẽ tự cài packages lần đầu và khởi động tại `http://localhost:8000`

---

## Cài đặt thủ công

```bat
cd hackathon

:: Tạo virtual environment (khuyến nghị)
python -m venv venv
venv\Scripts\activate

:: Cài packages
pip install -r backend\requirements.txt

:: Chạy server
cd backend
python main.py
```

---

## API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/` | Frontend HTML |
| POST | `/api/chat` | Main agent (SSE stream) |
| GET | `/api/bookings` | Danh sách booking |
| GET | `/api/health` | Health check |
| GET | `/api/destinations` | Tất cả destinations |
| GET | `/api/resorts/{dest_id}` | Resorts theo destination |
| GET | `/api/rooms/{resort_id}` | Rooms theo resort |
| GET | `/api/availability` | Lịch availability |
| GET | `/docs` | Swagger UI |

---

## Share qua Cloudflare Tunnel (không cần tài khoản)

Cloudflare Tunnel cho phép tạo public URL miễn phí, không cần cài server.

### Bước 1 — Tải cloudflared

Tải file `cloudflared-windows-amd64.exe` tại:
```
https://github.com/cloudflare/cloudflared/releases/latest
```

Đổi tên thành `cloudflared.exe` và đặt vào thư mục hackathon (hoặc bất kỳ đâu có trong PATH).

### Bước 2 — Chạy tunnel (terminal riêng, sau khi server đã chạy)

```bat
cloudflared tunnel --url http://localhost:8000
```

Cloudflare sẽ tạo URL dạng:
```
https://random-name-123.trycloudflare.com
```

**Share URL đó cho người khác** — họ mở trực tiếp trên điện thoại/máy tính, không cần cài gì.

> URL tồn tại đến khi bạn tắt terminal.

### Lưu ý khi demo qua Tunnel

- Backend phải đang chạy ở localhost:8000 trước
- URL tunnel mới mỗi lần khởi động cloudflared
- Người dùng truy cập URL tunnel → FastAPI serve HTML → HTML gọi API cùng origin → hoạt động bình thường

---

## Architecture

```
hackathon/
├── myvinpearl-ai-chatbot.html  ← Frontend (React + Tailwind CDN)
├── backend/
│   ├── main.py        ← FastAPI server (serve HTML + API)
│   ├── agent.py       ← LangGraph StateGraph
│   │   ├── classify_node  (OpenAI GPT-4o-mini, structured output)
│   │   ├── search_node    (mock DB + scoring)
│   │   ├── change_node    (booking lookup + availability)
│   │   └── cancel_node    (refund calculation + LLM policy explain)
│   ├── mock_db.py     ← Mock database (5 destinations, 5 resorts, rooms)
│   ├── tools.py       ← Scoring algorithms (pure Python)
│   └── requirements.txt
├── .env               ← API keys (không commit)
├── .env.example       ← Template
└── start.bat          ← Windows startup script
```

## LangGraph Flow

```
User input
    │
    ▼
[classify_node] ← GPT-4o-mini (structured output)
    intent, confidence, entities, thinking_steps
    │
    ▼ (router)
    ├─ search  → [search_node]  → destinations cards
    ├─ change  → [change_node]  → booking + dates
    └─ cancel  → [cancel_node]  → booking + refund + LLM policy
```

## SSE Event Format

```json
{"type": "thinking_start"}
{"type": "thinking_item", "text": "4 người (gia đình)", "ok": true}
{"type": "thinking_item", "text": "chưa có địa điểm", "ok": false}
{"type": "thinking_progress", "value": 60}
{"type": "thinking_progress", "value": 100}
{"type": "result", "intent": "search", "ui_state": "show_destinations", "result_data": {...}}
```

---

## Troubleshooting

**Lỗi: OPENAI_API_KEY chưa được đặt**
→ Kiểm tra file `.env` có đúng key chưa. Key bắt đầu bằng `sk-proj-...`

**Lỗi: ModuleNotFoundError**
→ Chạy `pip install -r backend\requirements.txt` từ thư mục hackathon

**Lỗi: Port 8000 đang được dùng**
→ Đổi PORT trong `.env`: `PORT=8001` hoặc kill process đang dùng cổng 8000

**Mở file HTML trực tiếp (không qua server)**
→ App tự detect và dùng mock data, không cần API. Đủ để demo UI.

**Cloudflare Tunnel báo lỗi connection refused**
→ Đảm bảo server đang chạy ở localhost:8000 trước khi chạy cloudflared
