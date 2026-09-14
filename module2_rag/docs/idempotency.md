# Idempotency trong API

## Khái niệm

Một thao tác được gọi là idempotent nếu thực hiện nó nhiều lần cho ra
cùng kết quả như thực hiện một lần. Trong HTTP, các method GET, PUT, DELETE
được thiết kế idempotent, còn POST thì không. Vấn đề xảy ra khi client gửi
POST tạo đơn hàng, mạng timeout, client retry, và server tạo hai đơn hàng.

## Idempotency key

Cách chuẩn để làm POST an toàn khi retry là dùng idempotency key. Client
sinh một UUID cho mỗi thao tác nghiệp vụ và gửi kèm trong header
`Idempotency-Key`. Server lưu key này cùng kết quả xử lý vào một bảng có
ràng buộc unique trên key.

Khi nhận request, server kiểm tra key đã tồn tại chưa. Nếu chưa, xử lý bình
thường rồi lưu key và response. Nếu key đã tồn tại và request trước đã hoàn
tất, server trả lại đúng response đã lưu mà không xử lý lại. Nếu request
trước còn đang chạy, server trả về 409 Conflict.

## Thời hạn lưu key

Idempotency key không cần lưu vĩnh viễn. Thông thường các hệ thống thanh toán
như Stripe giữ key trong 24 giờ, sau đó xoá. Client retry sau khoảng thời
gian đó phải sinh key mới. Nên chạy một job dọn dẹp định kỳ để xoá các key
quá hạn, tránh bảng phình to.

## Sai lầm thường gặp

Dùng chính nội dung request làm key (hash body) là sai, vì hai thao tác khác
nhau nhưng trùng nội dung sẽ bị coi là một. Key phải do client chủ động sinh
theo từng ý định nghiệp vụ.
