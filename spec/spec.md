# SPEC — MyVinpearl AI Booking Assistant

**Track:** Travel & Hospitality · **App thật:** MyVinpearl  
**Nhóm:** E403 - Nhóm F6 · **Ngày:** 04/06/2026

---

## 1. Bằng chứng

### Trải nghiệm trực tiếp (self-use)

| Quan sát | Nguồn | Path liên quan | Điều học được |
|----------|-------|----------------|---------------|
| Tìm khách sạn Hà Nội ngày 05–08/06, 1 phòng 1 khách → app trả về "Không có kết quả tìm kiếm phù hợp" kèm nút "Quay lại tìm kiếm", không có gợi ý thay thế, không giải thích lý do. | Self-use ([e_01.jpg](evidence/e_01.jpg)) | Failure path | Dead-end hoàn toàn — hệ thống báo lỗi nhưng không giúp user thoát ra. |
| Tìm combo vé máy bay + khách sạn phải nhập thủ công từng trường riêng lẻ: điểm đi, điểm đến, ngày nhận phòng, ngày trả phòng, số phòng, số người lớn, trẻ em, em bé, hạng vé. Không có AI hỗ trợ trích xuất từ câu tự nhiên. | Self-use ([e_02.jpg](evidence/e_02.jpg)) | Happy path (manual) | Toàn bộ việc parse intent đang đổ lên vai user — đây là cơ hội AI lớn nhất. |

### Đánh giá bên ngoài (App Store)

| Trích dẫn | Nguồn | Pain |
|-----------|-------|------|
| "Gây khó hiểu, lại lag, mục hỗ trợ khách hàng thì vô tích sự" ★☆☆☆☆ | App Store · Báo Min ([review1.jpg](evidence/review1.jpg)) | UX phức tạp, hỗ trợ yếu |
| "THÔNG TIN KO RÕ RÀNG, BẦM VÔ ĐƠN HÀNG KO THẤY NGÀY ĐI. MUA VÉ VINWONDER KÈM ĐẶT PHÒNG BỊ ÉP ĐI VÀO NGÀY CHECK IN PHÒNG" ★☆☆☆☆ | App Store · Thi Nguyễn ([review2.jpg](evidence/review2.jpg)) | Thông tin booking mờ, ngày không khớp |
| "Voucher Grand World hiển thị trên hệ thống nhưng các shop hết lượt, hết thời gian" ★☆☆☆☆ | App Store · Tình Võ ([review3.jpg](evidence/review3.jpg)) | Trạng thái inventory không chính xác |

### Benchmark đối thủ

| Sản phẩm | Pattern học được | Áp dụng được trong 1 ngày? |
|----------|-----------------|---------------------------|
| Expedia AI | Augmented decision — AI gợi ý, user click book; clarifying questions khi thiếu thông tin; human escalation khi phức tạp | Có — UI action cards + prompt clarification + mock data |
| Airbnb Support Bot | Hybrid — AI tự động routine, escalate complex; action cards cho đổi/hủy | Có — Action cards + escalation pattern |
| Hopper HT Assist | Chat + nút xác nhận; AI đề xuất rebook/refund, user click confirm | Có — Mock data + confirmation buttons |
| Perplexity AI | Inline citations luôn hiển thị (tránh hallucination); hiển thị "Đang tra cứu..." | Có — Hiển thị nguồn policy đang dùng |

**Insight tổng hợp:** Người dùng không muốn nhớ quy trình booking nhiều bước — họ muốn mô tả nhu cầu bằng ngôn ngữ tự nhiên như nói chuyện với nhân viên tư vấn. Điểm gãy nằm ở hai chỗ: đầu vào (nhập form thủ công) và sau booking (không hiểu policy đổi/hủy).

---

## 2. Lát cắt để build

> Cho khách du lịch đang tìm kiếm hoặc quản lý booking trên MyVinpearl, prototype dùng AI để **hỗ trợ tìm kiếm phòng bằng ngôn ngữ tự nhiên và giải thích yêu cầu đổi/hủy booking**, tạo ra danh sách lựa chọn kèm giải thích chính sách áp dụng, và xử lý trường hợp thiếu thông tin bằng cách hỏi lại thay vì tự suy đoán.

Một người dùng · một công việc · một quyết định AI đưa ra · một kết quả trả về:

> _"Tôi muốn đi Phú Quốc cuối tuần này 2 người"_ → AI trích xuất `{điểm_đến: Phú Quốc, ngày: cuối tuần, số_khách: 2}` → trả về danh sách phòng phù hợp kèm giá.

---

## 3. AI Product Canvas

| Ô | Nội dung |
|---|----------|
| **Value — Giá trị** | Dành cho khách du lịch cá nhân/gia đình đặt phòng Vinpearl. Pain: phải nhập form nhiều trường, không hiểu policy đổi/hủy, bị dead-end khi search thất bại. AI giải được: tự parse câu tự nhiên thành query tìm kiếm, giải thích policy bằng ngôn ngữ đơn giản, gợi ý thay thế khi không có kết quả — những việc form truyền thống không làm được. |
| **Trust — Niềm tin** | Khi AI trả lời sai chính sách hoàn tiền: (1) UI luôn hiển thị nguồn policy đang dùng để user tự kiểm tra; (2) AI nêu rõ mức độ chắc chắn ("Theo chính sách hiện tại…"); (3) Nút "Liên hệ hỗ trợ" luôn hiển thị khi AI không chắc; (4) User có thể sửa lại thông tin và agent cập nhật kết quả ngay. |
| **Feasibility — Tính khả thi** | Chi phí: GPT-4o-mini ~$0.00015/1K token — mỗi lượt chat ≈ $0.001, chấp nhận được cho demo. Độ trễ: classify + search ≈ 1–2 giây với SSE streaming. Dữ liệu cần có: mock DB 5 điểm đến + policy văn bản — đủ để demo. Rủi ro lớn nhất: AI hallucinate thông tin hoàn tiền sai → xử lý bằng cách luôn cite nguồn và fallback sang CSKH. Dừng lại nếu: chi phí API vượt $5/ngày hoặc độ trễ > 5 giây. |
| **Tín hiệu học** | Khi user sửa thông tin ("không phải 2 người, là 4 người") → agent ghi nhận correction và update kết quả ngay trong session. Dữ liệu correction được log vào `tests/graded_cases.json` để cải thiện prompt và test regression sau này. |

---

## 4. Tăng năng lực hay tự động hóa

**Quyết định: Augmentation (tăng năng lực)**

AI chỉ gợi ý và chuẩn bị thông tin — người dùng giữ quyền quyết định cuối cùng ở mọi bước.

**Lý do:** Booking và cancellation là tác vụ có rủi ro tài chính thực tế. Prototype Day 06 không thực hiện đặt phòng hoặc hủy thật — AI chỉ trích xuất thông tin, gợi ý lựa chọn, và giải thích chính sách. Nếu AI tự hành động (automation) và sai → user mất tiền hoặc mất phòng, hậu quả không thể hoàn tác dễ dàng.

**Human role:** Decider + Reviewer — xác nhận mọi thao tác thay đổi booking.

---

## 5. Bốn đường đi của trải nghiệm

| Đường đi | Kịch bản | Prototype xử lý |
|----------|----------|----------------|
| **Đường thuận** | User nhập: "Tôi muốn đi Phú Quốc cuối tuần này 2 người" | AI trích xuất `{Phú Quốc, cuối tuần, 2 khách}`, hiển thị danh sách phòng phù hợp dạng cards với giá và link đặt phòng |
| **Khi AI không chắc** | User nhập: "Tôi muốn đổi booking" | AI nhận ra thiếu thông tin, hỏi lại: "Bạn muốn đổi booking nào? Mã đặt phòng hoặc ngày đặt là gì?" — không tự suy đoán |
| **Khi AI sai** | User hỏi policy không có trong dữ liệu hoặc booking không tìm thấy | AI thông báo rõ: "Tôi không tìm thấy booking này trong hệ thống" + hiển thị nút "Liên hệ hỗ trợ Vinpearl" |
| **Khi người dùng sửa** | User sửa: "Không phải 2 người, là 4 người" | Agent nhận correction, cập nhật lại kết quả tìm kiếm ngay lập tức, log correction vào test cases |

---

## 6. Những kiểu lỗi đáng lo nhất

### Lỗi 1: AI đưa ra thông tin hoàn tiền sai

- **Khi nào xảy ra:** User hỏi "Tôi hủy booking này có được hoàn toàn bộ không?" khi policy phức tạp hoặc có điều kiện đặc biệt
- **Hậu quả:** User đưa ra quyết định tài chính sai, mất tiền, mất niềm tin vào sản phẩm
- **Xử lý:** Luôn hiển thị đoạn policy gốc đang dùng làm nguồn; nêu rõ mức độ chắc chắn; fallback sang "Liên hệ CSKH để xác nhận" nếu policy mơ hồ

### Lỗi 2: AI nhận diện sai intent dẫn đến wrong path

- **Khi nào xảy ra:** Câu nhập mơ hồ như "Cho tôi xem phòng" — không rõ search hay change hay cancel
- **Hậu quả:** User nhận kết quả không liên quan, phải nhập lại từ đầu
- **Xử lý:** Classify node trả về `confidence` score; nếu confidence < 0.7 thì hỏi lại thay vì đoán; hiển thị intent đã nhận diện để user xác nhận

### Lỗi 3: Dữ liệu mock không phản ánh thực tế

- **Khi nào xảy ra:** User hỏi phòng cụ thể, ngày cụ thể không có trong mock DB
- **Hậu quả:** AI báo không có phòng dù thực tế có, gây hiểu lầm về sản phẩm
- **Xử lý:** Ghi chú rõ trong UI "Đây là dữ liệu demo — không phản ánh inventory thực tế của Vinpearl"; agent giải thích rõ khi không tìm thấy kết quả

---

## 7. Kế hoạch kiểm thử và bằng chứng demo

### Đầu vào chuẩn bị sẵn cho demo

**Happy path:**
> "Tôi muốn đi Phú Quốc cuối tuần này, 2 người lớn 1 trẻ em, có bãi biển đẹp"

Kết quả kỳ vọng: AI trích xuất đúng `{Phú Quốc, 2 người lớn + 1 trẻ em, view biển}`, trả về ít nhất 2–3 gợi ý phòng phù hợp.

**Error/correction path:**
> "Tôi muốn hủy booking, tôi có được hoàn tiền không?"

Kết quả kỳ vọng: AI hỏi lại mã booking, sau khi nhận được thì giải thích policy hoàn tiền với citation nguồn rõ ràng, không tự khẳng định số tiền cụ thể.

### Bằng chứng lưu trong repo

| Loại | Vị trí | Nội dung |
|------|--------|----------|
| App Store reviews | `spec/evidence/review1–8.jpg` | Bằng chứng pain point từ user thật |
| Self-use screenshots | `spec/evidence/e_01.jpg`, `e_02.jpg` | Dead-end search + form phức tạp |
| Test cases | `codebase/tests/` | Happy path, failure path, correction cases |
| Graded cases | `codebase/data/graded_cases.json` | Các trường hợp đã kiểm thử và đánh giá |
| Demo slides | `spec/demo-slides.html` | Kịch bản trình bày |

---

## 8. Phân công

| Thành viên | Phụ trách | Bằng chứng trong repo |
|------------|-----------|----------------------|
| Thành viên 1 | Viết và kiểm thử prompt (`backend/agent/prompts.py`), xây dựng LangGraph agent (`backend/agent/graph.py`, `nodes.py`), định nghĩa policy KB (`data/POLICY.md`, `backend/policy.py`) | Prompt files, policy data, agent graph |
| Thành viên 2 | Dựng giao diện chatbot (`myvinpearl-ai-chatbot.html`), thiết kế SSE streaming UI, tích hợp frontend–backend | Screenshot UI, HTML file, interaction flow |
| Thành viên 3 | Viết kịch bản demo, soạn test cases (`tests/`), kiểm thử failure path và correction path, giữ repo và nộp bài | Test files, demo script, graded_cases.json |
| Cả nhóm | SPEC, evidence pack, demo day | spec.md, evidence/, demo-slides.html |
