# User Flow — Đặt phòng qua AI Chatbot MyVinpearl

## Tổng quan

AI Agent xử lý ngôn ngữ tự nhiên → trích xuất intent + entities → routing thông minh → hiển thị rich UI cards ngay trong giao diện chat.

---

## Sơ đồ luồng (Mermaid)

```mermaid
flowchart TD
    U([👤 User nhắn tin]) --> CL

    subgraph AGENT ["🧠 AI Agent — LangGraph"]
        CL["Classify Node\nIntent + Entities\nwith_structured_output"]
        CL --> CONF{Confidence ≥ 0.6\n& đủ thông tin?}

        CONF -- "LOW-CONFIDENCE PATH\n❓ Thiếu địa điểm/ngày\n   hoặc unclear" --> CLR["Clarify Node\nbind_tools: none\nLLM hỏi 1 câu cụ thể"]
        CONF -- "HIGH CONFIDENCE" --> RT

        RT{Route by intent}
        RT -- search --> SN["Search Node\nbind_tools: search_hotels\nLLM gọi tool → đọc kết quả\n→ sinh llm_response"]
        RT -- correction --> SN
        RT -- change --> CHN["Change Node\nbind_tools: get_booking\n          check_available_dates"]
        RT -- cancel --> CAN["Cancel Node\nbind_tools: calculate_refund"]
        RT -- qa --> QAN["QA Node\nKnowledge base answer\nNo tools needed"]
    end

    CLR -->|ui_state: ask_clarification| CW["💬 Chat: Câu hỏi cụ thể\n+ quick reply buttons\n📍 Phú Quốc / Nha Trang / Đà Nẵng"]
    CW -->|User trả lời| U

    SN -->|ui_state: show_destinations| DC["📍 DestinationsWidget\n3 cards: match score + ảnh + lý do"]
    DC -->|User chọn điểm đến| HT["🏨 HotelsWidget\nHorizontal scroll cards\ngiá + rating"]
    HT -->|User chọn hotel| RM["🛏 RoomsWidget\nảnh phòng + capacity + giá/đêm"]
    RM -->|User chọn phòng| CHK{User info\ncomplete?}

    CHK -- "Thiếu tên/email" --> UIF["📋 UserInfoWidget\nForm pre-filled từ profile\nEditable inputs + validate"]
    CHK -- "Đã có đủ" --> BC
    UIF -->|Confirm| BC["📑 BookingConfirmWidget\nHotel ảnh + checkin/out\nTên / Email / Tổng tiền\n✓ Xác nhận   Hủy"]

    BC -->|✓ Xác nhận| API["POST /api/book"]
    API --> SUC(["✅ BookingSuccessWidget\nMã VNP-2026-XXXX\nEmail xác nhận đã gửi"])
    BC -->|Hủy| DC

    CHN -->|found| CD["📅 Show available dates\n+ Change policy\nllm_response: giải thích"]
    CHN -->|not found| FL

    CAN -->|found| CR["💰 Show refund calculation\n+ Policy tiers\nllm_response: giải thích"]
    CAN -->|not found| FL

    QAN -->|ui_state: show_message| MSG["💬 Conversational answer\n+ gợi ý action tiếp theo"]

    FL(["❌ FailureWidget\nllm_response đồng cảm\n📞 1800 1234 — Gọi CSKH\n💬 Chat với nhân viên\n🔗 vinpearl.com/ho-tro"])

    style SUC fill:#d1fae5,stroke:#059669,color:#065f46
    style FL fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    style CW fill:#eff6ff,stroke:#3b82f6
    style UIF fill:#fef9c3,stroke:#ca8a04
    style BC fill:#fff7ed,stroke:#ea580c
```

---

## 4 Paths theo Spec

### 1. Happy Path ✅
```
User: "Tôi muốn đi Phú Quốc cuối tuần này 2 người"
  → Classify: intent=search, confidence=0.92
  → Search Node: LLM gọi search_hotels(destination="Phú Quốc", guest_count=2)
  → DestinationsWidget → HotelsWidget → RoomsWidget
  → UserInfoWidget (pre-fill: Nguyễn Mai Hồng Trâm / gmail.com)
  → BookingConfirmWidget (1 đêm, 2 người, tổng giá)
  → POST /api/book → VNP-2026-XXXX ✅
```

### 2. Low-confidence Path ❓
```
User: "Muốn đổi booking"
  → Classify: intent=change, confidence=0.55, clarification_needed=True
  → Clarify Node: "Bạn muốn đổi booking nào? Có mã VNP-... không?"
  → Quick replies: ["Tìm booking tự động", "Nhập mã booking"]
  
User: "VNP-2024-8821"
  → Classify: intent=change, confidence=0.95, booking_ref=VNP-2024-8821
  → Change Node → Available dates → Chọn ngày mới ✅
```

### 3. Failure Path ❌
```
User: "Hủy booking VNP-9999-8888"
  → Classify: intent=cancel, booking_ref=VNP-9999-8888
  → Cancel Node: get_booking_and_refund() → not found
  → LLM sinh câu trả lời đồng cảm
  → FailureWidget: "Không tìm thấy booking này..."
    [📞 Gọi 1800 1234] [💬 Chat nhân viên] [🔄 Thử mã khác]

User: "Chính sách hoàn tiền cho phòng ngày lễ là gì?"
  → Classify: intent=qa
  → QA Node: "Chính sách này chưa có trong dữ liệu hiện tại..."
  → FailureWidget (policy_not_found)
    [🔗 Xem đầy đủ tại vinpearl.com/chinh-sach]
```

### 4. Correction Path 🔄
```
User: "Tìm resort biển 2 người"
  → Search → DestinationsWidget (score cho 2 người)

User: "Không phải 2 người, là 4 người gia đình"
  → Classify: intent=correction, entities={guest_count:4, trip_type:family}
  → Search Node: merge {previous_entities + guest_count:4 + trip_type:family}
  → LLM: "Đã cập nhật! Với 4 người gia đình, đây là kết quả mới..."
  → DestinationsWidget (score mới, family-friendly cao hơn) ✅
```

---

## Cấu trúc Backend Agent

```
backend/agent/
  __init__.py      — public API: stream_agent_events, run_agent
  schemas.py       — AgentState, IntentResult (6 intents + clarification_needed)
  prompts.py       — CLASSIFY, SEARCH, CHANGE, CANCEL, QA, CLARIFY, FAILURE
  tools.py         — @tool: search_hotels, get_booking, calculate_refund, check_available_dates
  nodes.py         — classify, search (+ correction), change, cancel, qa, clarify, error
  graph.py         — LangGraph StateGraph
  stream.py        — SSE generator cho FastAPI
```

## Cấu trúc Frontend Chat (trong HTML)

```
Message types rendered in chat:
  'text'            → standard bubble
  'destinations'    → DestinationsWidget (3 cards + match score)
  'hotels'          → HotelsWidget (horizontal scroll)
  'rooms'           → RoomsWidget (vertical cards + images)
  'user_info'       → UserInfoWidget (pre-filled, editable, validates)
  'booking_confirm' → BookingConfirmWidget (full summary + confirm/cancel)
  'booking_success' → BookingSuccessWidget (green card + ref)
  'failure'         → FailureWidget (red card + CSKH escalation)
```
