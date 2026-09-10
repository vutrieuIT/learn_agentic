# Connection pool cho database

## Vì sao cần pool

Mở một kết nối TCP tới Postgres rồi bắt tay xác thực tốn khoảng 20 tới 50
mili giây. Nếu mỗi request HTTP đều mở kết nối mới rồi đóng, phần lớn thời
gian xử lý bị lãng phí vào việc thiết lập kết nối. Connection pool giữ sẵn
một tập kết nối đã mở và cho các request mượn rồi trả lại.

## Các tham số quan trọng

`min_size` là số kết nối luôn giữ mở kể cả khi rảnh. `max_size` là trần số
kết nối; khi tất cả đang bận, request mới phải xếp hàng chờ. Đặt `max_size`
quá cao sẽ làm Postgres cạn `max_connections` phía server, mặc định chỉ 100.

`timeout` hay `acquire_timeout` là thời gian tối đa một request chờ để lấy
được kết nối từ pool trước khi bị lỗi. Giá trị phổ biến là 30 giây.
`max_lifetime` buộc đóng và mở lại kết nối sau một khoảng thời gian, thường
30 phút, để tránh kết nối cũ bị firewall hoặc load balancer cắt ngầm.

## Tính kích thước pool

Công thức thường dùng: số kết nối bằng số CPU core của database nhân hai,
cộng thêm số ổ đĩa. Với server 4 core thì pool khoảng 9 tới 10 kết nối cho
mỗi instance ứng dụng là hợp lý. Nhiều hơn thường không tăng throughput mà
chỉ tăng tranh chấp.

## Dấu hiệu pool sai cấu hình

Nếu log xuất hiện lỗi timeout khi acquire kết nối, hoặc latency tăng vọt
dưới tải, khả năng cao `max_size` quá nhỏ hoặc có query chạy lâu giữ kết nối
không trả. Bật log query chậm để tìm nguyên nhân giữ kết nối.
