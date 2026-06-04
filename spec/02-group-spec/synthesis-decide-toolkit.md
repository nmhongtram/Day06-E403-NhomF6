# Toolkit — Từ Evidence Đến Build Slice

## 1. Gom evidence thành cụm

### Cụm 1: Khó tìm kiếm và đặt dịch vụ bằng giao diện hiện tại

* User phải nhập nhiều trường thông tin thủ công khi tìm vé/phòng.
* Không hỗ trợ nhập bằng ngôn ngữ tự nhiên.
* User phải hiểu trước quy trình booking mới sử dụng được.

### Cụm 2: Không được hỗ trợ khi tìm kiếm thất bại

* Hệ thống chỉ báo "Không có kết quả phù hợp".
* Không giải thích nguyên nhân.
* Không gợi ý ngày khác, khách sạn khác hoặc lựa chọn thay thế.

### Cụm 3: Không hiểu chính sách đổi/hủy sau khi đặt

* Review phản ánh thông tin đơn hàng khó hiểu.
* Điều kiện sử dụng combo/voucher không rõ ràng.
* User không biết có được hoàn tiền hay không khi muốn hủy.

### Cụm 4: Hỗ trợ khách hàng chưa hiệu quả

* Review đề cập mục hỗ trợ khách hàng "vô tích sự".
* User phải tự tìm chính sách hoặc liên hệ CSKH.
* Thiếu lớp hỗ trợ tức thời cho các câu hỏi phổ biến.

---

## 2. Viết insight

User đặt phòng hoặc vé máy bay trên MyVinpearl không chỉ cần công cụ tìm kiếm và đặt dịch vụ.

Họ thật ra cần một trợ lý có thể hiểu nhu cầu bằng ngôn ngữ tự nhiên và giải thích các quyết định liên quan đến booking một cách dễ hiểu,

vì nhiều evidence cho thấy người dùng gặp khó khăn khi nhập nhiều thông tin tìm kiếm, không được hỗ trợ khi tìm kiếm thất bại và thường không hiểu các điều kiện đổi/hủy hoặc hoàn tiền sau khi đặt.

---

## 3. Viết opportunity

Cơ hội là dùng AI để augment quy trình đặt phòng/vé và hỗ trợ đổi/hủy booking,

giúp người dùng tìm kiếm dịch vụ nhanh hơn, hiểu chính sách dễ hơn và biết bước tiếp theo cần thực hiện,

trong khi vẫn kiểm soát rủi ro bằng cách yêu cầu xác nhận từ người dùng trước khi thực hiện bất kỳ hành động thay đổi booking nào.

---

## 4. Chọn build slice

### User

Khách du lịch cá nhân đã hoặc đang có nhu cầu đặt phòng/vé trên MyVinpearl.

### Task

Tìm kiếm phòng/vé bằng ngôn ngữ tự nhiên và hỏi về việc đổi/hủy booking.

### AI Decision

AI:

* Trích xuất thông tin từ câu chat.
* Hiển thị các lựa chọn phù hợp.
* Giải thích chính sách đổi/hủy.
* Đề xuất hành động tiếp theo.

User:

* Chọn phòng/vé.
* Xác nhận đổi/hủy.

### Failure Path

Người dùng cung cấp thông tin không đầy đủ hoặc mơ hồ:

Ví dụ:
"Tôi muốn đổi booking của tôi."

AI không biết:

* Booking nào.
* Đổi ngày nào.
* Đổi phòng hay đổi chuyến bay.

=> AI phải hỏi lại thay vì tự suy đoán.

### Evidence

* Self-use evidence về việc nhập liệu thủ công.
* Self-use evidence về search failure.
* Review phản ánh thông tin booking khó hiểu.
* Competitor pattern: Expedia AI, Airbnb Support Bot, Hopper HT Assist.

---

## 5. Quyết định: giữ, giảm scope, hay đổi hướng?

### Quyết định: Giảm scope

Giữ domain:
Travel & Hospitality.

Giảm từ:
"AI Concierge hỗ trợ toàn bộ hành trình du lịch."

Xuống còn:

"AI Booking Assistant hỗ trợ tìm kiếm phòng/vé bằng ngôn ngữ tự nhiên và giải thích quy trình đổi/hủy booking."

Lý do:

* Có evidence rõ.
* Có AI fit rõ.
* Demo được trong 3–5 phút.
* Build được trong 1 ngày.
* Có thể thiết kế đầy đủ happy path và failure path.

---

## 6. Câu chốt cuối

Dựa trên evidence từ trải nghiệm sử dụng MyVinpearl, các review App Store và phân tích đối thủ,

nhóm sẽ build AI Booking Assistant hỗ trợ tìm kiếm phòng/vé bằng ngôn ngữ tự nhiên và giải thích quy trình đổi/hủy booking,

cho khách du lịch sử dụng MyVinpearl,

để giải quyết việc nhập liệu phức tạp và khó hiểu chính sách sau khi đặt,

bằng cách AI augment quá trình tìm kiếm và hỗ trợ ra quyết định,

và sẽ test failure path khi người dùng cung cấp thông tin booking không đầy đủ hoặc mơ hồ.

---

## 7. Backlog

Những thứ KHÔNG build trong Day 06:

* Tích hợp hệ thống đặt phòng thật.
* Thanh toán thật.
* Kết nối API hãng hàng không thật.
* Hoàn tiền thật.
* Tự động đổi/hủy booking trên hệ thống thật.
* Cá nhân hóa theo lịch sử khách hàng.
* Multi-agent travel planning.
* Gợi ý lịch trình du lịch.
