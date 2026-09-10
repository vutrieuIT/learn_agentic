# Message queue

## Vì sao dùng queue

Message queue đặt giữa producer và consumer, cho phép hai bên chạy độc lập.
Khi lượng request tăng đột biến, producer đẩy việc vào queue rất nhanh rồi
trả lời người dùng ngay, còn consumer xử lý dần theo tốc độ của mình. Queue
đóng vai trò bộ đệm hấp thụ tải và giảm khớp nối giữa các dịch vụ.

## At-least-once và idempotency

Phần lớn broker như RabbitMQ, SQS, Kafka bảo đảm giao ít nhất một lần. Nghĩa
là một message có thể được giao lại nếu consumer xử lý xong nhưng chưa kịp
báo ack, hoặc bị timeout. Do đó consumer phải xử lý idempotent: cùng một
message chạy hai lần không được gây tác dụng phụ kép. Thường lưu id message
đã xử lý vào một bảng để bỏ qua bản trùng.

## Dead letter queue

Nếu một message làm consumer lỗi liên tục, nó sẽ bị giao lại mãi và chặn cả
hàng đợi. Cấu hình số lần thử lại tối đa, thường 3 tới 5 lần, sau đó chuyển
message sang dead letter queue để điều tra riêng, không làm nghẽn luồng
chính.

## Thứ tự message

Queue thông thường không bảo đảm thứ tự tuyệt đối khi có nhiều consumer chạy
song song. Kafka giữ thứ tự trong phạm vi một partition, và message cùng một
khoá được đưa vào cùng partition. Nếu nghiệp vụ cần xử lý theo đúng thứ tự
cho mỗi người dùng, hãy dùng user id làm khoá phân vùng.

## Khi nào không cần queue

Nếu công việc phải trả kết quả ngay cho người dùng trong cùng request, queue
chỉ thêm độ trễ và độ phức tạp. Queue hợp với việc chạy nền như gửi email,
sinh báo cáo, xử lý ảnh.
