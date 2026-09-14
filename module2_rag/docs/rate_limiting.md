# Rate limiting

## Mục đích

Rate limiting giới hạn số request một client được thực hiện trong một khoảng
thời gian, để bảo vệ hệ thống khỏi lạm dụng, tấn công từ chối dịch vụ, và để
phân bổ tài nguyên công bằng giữa người dùng. Server trả về mã 429 Too Many
Requests khi client vượt hạn mức, thường kèm header `Retry-After` cho biết
nên chờ bao lâu.

## Token bucket

Thuật toán phổ biến nhất là token bucket. Mỗi client có một xô chứa tối đa N
token, được nạp lại đều đặn với tốc độ R token mỗi giây. Mỗi request tiêu một
token; nếu xô rỗng thì request bị từ chối. Token bucket cho phép các đợt bùng
ngắn miễn là trung bình không vượt R, điều mà giới hạn cứng theo cửa sổ cố
định không làm được.

## Fixed window và sliding window

Fixed window đếm request theo từng khối thời gian, ví dụ mỗi phút. Cách này
đơn giản nhưng có lỗi biên: client có thể gửi gấp đôi hạn mức quanh thời điểm
chuyển phút. Sliding window log lưu mốc thời gian từng request và đếm số
request trong 60 giây gần nhất, chính xác hơn nhưng tốn bộ nhớ hơn.

## Rate limit phân tán

Khi có nhiều instance ứng dụng, bộ đếm phải nằm ở kho dùng chung, thường là
Redis với lệnh INCR kèm EXPIRE, hoặc script Lua để thao tác nguyên tử. Đặt
bộ đếm trong bộ nhớ từng instance sẽ cho hạn mức thực tế lớn gấp số instance.

## Đặt hạn mức ở đâu

Nên rate limit theo API key hoặc user id thay vì theo địa chỉ IP, vì nhiều
người dùng có thể chia sẻ một IP qua NAT, và một kẻ tấn công có thể đổi IP.
IP chỉ nên dùng cho các endpoint chưa xác thực như đăng nhập.
