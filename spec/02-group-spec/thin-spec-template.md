# Template — Thin SPEC Cuối Day 05

## 1. Track, product/app và user

**Track:** Travel & Hospitality

**Product/app thật:** MyVinpearl

**User cụ thể:**
Khách du lịch cá nhân hoặc gia đình đang tìm kiếm và đặt phòng khách sạn/combo vé máy bay + khách sạn trên MyVinpearl.

**Nhóm có phải user thật không? Nếu không, khác ở đâu?**

Nhóm chỉ là người dùng thử nghiệm để thực hiện workflow booking.

User thực tế thường:

* Có kế hoạch du lịch thật.
* Đã hoặc sắp thanh toán booking.
* Quan tâm đến điều kiện đổi/hủy và hoàn tiền.

Trong khi nhóm không chịu rủi ro tài chính thực tế khi thay đổi hoặc hủy booking.

---

## 2. Evidence summary

| Evidence                                                                                     | Nguồn               | User/pain nói lên điều gì?                                            | SPEC phải đổi gì?                                                   |
| -------------------------------------------------------------------------------------------- | ------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------- |
| User phải nhập nhiều trường thông tin khi tìm kiếm combo vé + khách sạn                      | Self-use            | Booking flow phức tạp, user phải tự điền và hiểu nhiều trường dữ liệu | Thêm AI parse ngôn ngữ tự nhiên thành thông tin booking             |
| Search thất bại chỉ hiện "Không có kết quả phù hợp"                                          | Self-use            | User bị dead-end, không biết phải làm gì tiếp theo                    | AI cần giải thích nguyên nhân và đề xuất phương án thay thế         |
| Review phản ánh thông tin booking và điều kiện sử dụng không rõ ràng                         | App Store Review    | User khó hiểu đơn hàng và chính sách sau khi đặt                      | AI hỗ trợ giải thích booking và chính sách đổi/hủy                  |
| Expedia AI, Airbnb Support Bot, Hopper HT Assist đều hỗ trợ booking + modify/cancel qua chat | Competitor Analysis | Workflow booking support là use case đã được chứng minh               | Thu hẹp build slice vào booking support thay vì concierge tổng quát |

---

## 3. Pain statement

User muốn đặt phòng khách sạn hoặc combo vé máy bay + khách sạn trên MyVinpearl, nhưng gặp khó khăn trong việc nhập thông tin booking và hiểu các chính sách sau khi đặt, vì quy trình booking yêu cầu nhiều trường dữ liệu, hệ thống không hỗ trợ nhập bằng ngôn ngữ tự nhiên, và các điều kiện đổi/hủy thường được trình bày dài, khó hiểu.

Khi cần thay đổi kế hoạch, người dùng thường không biết:

* Booking của mình có được đổi ngày hay không.
* Hủy booking có bị mất phí hay không.
* Điều kiện hoàn tiền áp dụng như thế nào.

Điều này khiến họ phải tự đọc policy hoặc liên hệ bộ phận hỗ trợ khách hàng.

Bằng chứng chính:

* Self-use: User phải nhập thủ công nhiều trường khi tìm kiếm combo vé + khách sạn.
* Self-use: Search failure không có giải thích hoặc gợi ý tiếp theo.
* Review App Store: "Thông tin không rõ ràng", "bấm vào đơn hàng không thấy ngày đi", "bị ép ngày check-in", "hỗ trợ khách hàng vô tích sự".
* Competitor benchmark: Expedia AI, Airbnb Support Bot và Hopper HT Assist đều tập trung hỗ trợ booking modification và cancellation.

---

## 4. Build slice

Cho khách du lịch đang tìm kiếm hoặc quản lý booking trên MyVinpearl,

prototype sẽ dùng AI để hỗ trợ tìm kiếm phòng/vé bằng ngôn ngữ tự nhiên và giải thích yêu cầu đổi/hủy booking,

tạo ra danh sách lựa chọn booking cùng giải thích chính sách áp dụng,

và xử lý trường hợp thiếu thông tin bằng cách hỏi lại thay vì tự suy đoán.

---

## 5. Auto/Aug decision

* [x] Augmentation
* [ ] Conditional automation
* [ ] Automation

### Lý do chọn

Booking và cancellation là tác vụ có rủi ro tài chính.

Prototype Day 06 không thực hiện đặt phòng hoặc hủy thật.

AI chỉ:

* Trích xuất thông tin.
* Gợi ý lựa chọn.
* Giải thích chính sách.
* Đề xuất bước tiếp theo.

Quyết định cuối cùng luôn thuộc về người dùng.

### Human role

Decider + Reviewer

---

## 6. Four paths

| Path           | Prototype phải thể hiện gì?                                                                                                         |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Happy          | User nhập: "Tôi muốn đi Phú Quốc cuối tuần này 2 người". AI trích xuất thông tin và hiển thị danh sách phòng/vé phù hợp.            |
| Low-confidence | User nhập: "Tôi muốn đổi booking". AI không đủ thông tin nên hỏi lại booking nào hoặc muốn đổi gì.                                  |
| Failure        | User hỏi chính sách không tồn tại trong dữ liệu hoặc booking không tìm thấy. AI thông báo không đủ dữ liệu và đề xuất liên hệ CSKH. |
| Correction     | User sửa thông tin: "Không phải 2 người, là 4 người". AI cập nhật lại kết quả tìm kiếm và ghi nhận correction.                      |

---

## 7. Failure mode nguy hiểm nhất

Nếu user hỏi:

"Tôi muốn hủy booking này, tôi có được hoàn tiền toàn bộ không?"

AI có thể hiểu sai chính sách đổi/hủy và đưa ra thông tin hoàn tiền không chính xác.

Hậu quả là:

* User đưa ra quyết định tài chính sai.
* Mất niềm tin vào sản phẩm.
* Khiếu nại với doanh nghiệp.

Prototype sẽ xử lý bằng:

* Hiển thị nguồn chính sách đang sử dụng.
* Giải thích mức độ chắc chắn.
* Yêu cầu user xác nhận.
* Fallback sang liên hệ nhân viên hỗ trợ nếu policy không rõ ràng.

Owner kiểm thử path này là: ___________

---

## 8. Owner plan cho sáng Day 06

| Thành viên   | Việc phụ trách                 | Bằng chứng cần có trong repo              |
| ------------ | ------------------------------ | ----------------------------------------- |
| Thành viên 1 | Prompt + Policy Knowledge Base | Prompt, mock policy data, test cases      |
| Thành viên 2 | Frontend Prototype             | Screenshot UI, interaction flow           |
| Thành viên 3 | Testing + Failure Path         | Failure log, correction cases, edge cases |
| Cả nhóm      | Demo script                    | Demo flow, happy path, failure path       |
| Cả nhóm      | SPEC & Submission              | spec-final.md, prototype-readme.md        |
