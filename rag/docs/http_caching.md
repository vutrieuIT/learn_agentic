# HTTP caching

## Cache-Control

Header `Cache-Control` quyết định ai được cache và trong bao lâu. `max-age=3600`
cho phép cache 1 giờ. `public` cho phép cả CDN và proxy cache, `private` chỉ
cho trình duyệt của người dùng. `no-store` cấm lưu hoàn toàn, dùng cho dữ liệu
nhạy cảm. `no-cache` cho phép lưu nhưng bắt buộc kiểm tra lại với server trước
khi dùng.

## Validation với ETag

Khi `max-age` hết hạn, client không nhất thiết phải tải lại toàn bộ. Server
gắn header `ETag` là một mã băm của nội dung. Lần sau client gửi lại mã đó
trong header `If-None-Match`. Nếu nội dung chưa đổi, server trả về 304 Not
Modified với body rỗng, tiết kiệm băng thông. `Last-Modified` và
`If-Modified-Since` hoạt động tương tự nhưng theo mốc thời gian.

## Cache ở tầng nào

Cache trình duyệt nhanh nhất nhưng chỉ phục vụ một người dùng. CDN cache phục
vụ nhiều người dùng ở gần biên mạng, phù hợp cho tài nguyên tĩnh và cả API
response công khai. Reverse proxy như Varnish hoặc nginx cache đặt trước ứng
dụng, giảm tải cho backend.

## Vô hiệu hoá cache

Vấn đề khó nhất của caching là invalidation. Chiến lược phổ biến là gắn phiên
bản vào URL của tài nguyên tĩnh, ví dụ `app.a1b2c3.js`, để khi nội dung đổi
thì URL đổi và cache cũ tự nhiên không còn được dùng. Với API, thường đặt
`max-age` ngắn hoặc dùng `no-cache` kèm ETag để luôn kiểm tra lại.
