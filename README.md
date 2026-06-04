# MyVinpearl AI Booking Assistant

Chatbot AI hỗ trợ đặt phòng, đổi/hủy và tra cứu chính sách hoàn tiền cho hệ thống Vinpearl — xây dựng trong hackathon Day 06.

---

## Thành viên nhóm

| Mã học viên | Họ và tên | Vai trò chính |
|-------------|-----------|---------------|
| 2A202600957 | Nguyễn Mai Hồng Trâm | Backend · AI Agent · Prompt engineering |
| 2A202600618 | Ngô Thị Ngọc Ánh | Frontend · Giao diện chatbot |
| 2A202600842 | Nguyễn Ngọc Anh | Testing · Kịch bản demo · SPEC |

---

## Phân công công việc

| Thành viên | Phụ trách | Chi tiết |
|------------|-----------|----------|
| Nguyễn Mai Hồng Trâm - 2A202600957 | Backend + Prompt | Xây dựng LangGraph agent (`backend/agent/`), viết và kiểm thử toàn bộ system prompt (`prompts.py`), định nghĩa policy hoàn tiền (`policy.py`, `data/POLICY.md`), dựng mock database (`mock_db.py`) |
| Ngô Thị Ngọc Ánh - 2A202600618 | Frontend | Xây dựng giao diện chatbot (`myvinpearl-ai-chatbot.html`), thiết kế luồng SSE streaming hiển thị thinking steps, tích hợp UI với backend API |
| Nguyễn Ngọc Anh - 2A202600842 | Testing + Demo | Viết test cases (`tests/`), kiểm thử failure path và correction path, soạn kịch bản demo (happy case + error case), quản lý repo và nộp bài |

---

## Cách chạy prototype

### Yêu cầu

- Python 3.10 trở lên
- OpenAI API key — lấy tại [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### Bước 1 — Cài đặt

```bat
cd codebase
copy .env.example .env
```

Mở file `.env` vừa tạo và điền API key:

```ini
OPENAI_API_KEY=sk-proj-xxx...
```

### Bước 2 — Cài thư viện

```bat
pip install -r requirements.txt
```

### Bước 3 — Chạy server

**Cách nhanh (Windows):** double-click `start.bat`

**Hoặc chạy thủ công:**

```bat
cd src
python main.py
```

Server khởi động tại **http://localhost:8000** — mở trình duyệt và vào địa chỉ này để dùng chatbot.

### Biến môi trường

| Biến | Bắt buộc | Mặc định | Mô tả |
|------|----------|----------|-------|
| `OPENAI_API_KEY` | Có | — | OpenAI API key, bắt đầu bằng `sk-proj-` |
| `OPENAI_MODEL_FAST` | Không | `gpt-4o-mini` | Model dùng cho intent classification |
| `OPENAI_MODEL_SMART` | Không | `gpt-4o-mini` | Model dùng cho giải thích policy |
| `PORT` | Không | `8000` | Cổng server |
| `HOST` | Không | `0.0.0.0` | Host server |

### Chạy tests

```bat
cd codebase
pytest tests/
```

### Chia sẻ qua Cloudflare Tunnel (không cần server)

Sau khi backend đang chạy tại localhost:8000:

```bat
cloudflared tunnel --url http://localhost:8000
```

Sẽ nhận được URL dạng `https://random-name.trycloudflare.com` — chia sẻ link này cho người khác truy cập trực tiếp.

---

## Công cụ và API sử dụng

### AI / Model

| Công cụ | Mục đích |
|---------|----------|
| **OpenAI GPT-4o-mini** | Model AI chính — phân loại intent, trích xuất thông tin, giải thích chính sách hoàn tiền |
| **LangGraph** | Orchestration AI agent theo state machine (classify → route → search/change/cancel) |
| **LangChain** | Tích hợp OpenAI, structured output, message formatting |

### Backend

| Công cụ | Mục đích |
|---------|----------|
| **FastAPI** | Web framework, REST API, SSE streaming |
| **Pydantic** | Validation dữ liệu, structured output schema |
| **python-dotenv** | Quản lý biến môi trường |

### Frontend

| Công cụ | Mục đích |
|---------|----------|
| **React 18** (CDN) | UI library — không cần build step |
| **Tailwind CSS** (CDN) | Styling, responsive design |
| **Server-Sent Events (SSE)** | Streaming thinking steps và kết quả theo thời gian thực |

### Triển khai

| Công cụ | Mục đích |
|---------|----------|
| **Cloudflare Tunnel** | Tạo public URL tức thì để share demo, không cần deploy server |

---

## Cấu trúc project

```
codebase/
├── myvinpearl-ai-chatbot.html   ← Frontend (React + Tailwind, load qua CDN)
├── requirements.txt             ← Python dependencies
├── src/
│   ├── main.py                  ← FastAPI server, SSE endpoint — entry point duy nhất
│   ├── agent/
│   │   └── graph.py             ← LangGraph ReAct agent (agent ⇄ tools loop)
│   ├── core/
│   │   ├── llm.py               ← LLM factory (get_llm / get_smart_llm)
│   │   └── schemas.py           ← Data models
│   └── utils/
│       ├── mock_db.py           ← Dữ liệu mẫu (5 điểm đến, phòng, booking)
│       ├── scoring.py           ← Thuật toán gợi ý phòng
│       ├── data_store.py        ← Business logic API (wraps mock_db + scoring)
│       └── policy.py            ← Load chính sách đổi/hủy từ data/POLICY.md
├── data/
│   ├── hotels.json              ← Danh sách resort
│   └── POLICY.md                ← Chính sách đổi/hủy
├── tests/                       ← Unit tests + test cases
├── .env.example                 ← Template biến môi trường
└── start.bat                    ← Script khởi động Windows
```

---

## Xử lý sự cố

| Lỗi | Cách sửa |
|-----|----------|
| `OPENAI_API_KEY chưa được đặt` | Kiểm tra file `.env` có key đúng định dạng `sk-proj-...` |
| `ModuleNotFoundError` | Chạy lại `pip install -r backend\requirements.txt` |
| `Port 8000 already in use` | Đổi `PORT=8001` trong `.env` hoặc tắt tiến trình đang dùng port 8000 |
| `Connection refused` (tunnel) | Đảm bảo backend đang chạy trước khi mở tunnel |
