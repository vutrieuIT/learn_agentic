# Index trong cơ sở dữ liệu quan hệ

## B-tree index

Index mặc định trong Postgres và MySQL là B-tree. Nó giữ các giá trị của cột
theo thứ tự sắp xếp trong một cây cân bằng, cho phép tìm một giá trị hoặc một
khoảng giá trị trong thời gian logarit thay vì quét toàn bảng. B-tree phục vụ
tốt các truy vấn dùng toán tử bằng, lớn hơn, nhỏ hơn, BETWEEN và cả ORDER BY
trên đúng cột được index.

## Composite index và thứ tự cột

Index nhiều cột chỉ dùng được hiệu quả khi truy vấn lọc theo tiền tố trái của
danh sách cột. Index trên `(user_id, created_at)` phục vụ được truy vấn lọc
theo `user_id`, hoặc theo cả `user_id` và `created_at`, nhưng không giúp gì
cho truy vấn chỉ lọc theo `created_at`. Quy tắc chung là đặt cột lọc bằng
trước, cột lọc khoảng sau.

## Chi phí của index

Mỗi index làm chậm INSERT, UPDATE, DELETE vì database phải cập nhật cả index.
Index cũng chiếm dung lượng đĩa, đôi khi bằng hoặc hơn dữ liệu gốc. Vì vậy
không nên tạo index cho mọi cột mà chỉ cho các cột thực sự xuất hiện trong
mệnh đề WHERE, JOIN hoặc ORDER BY của truy vấn chạy thường xuyên.

## Index không được dùng

Database bỏ qua index nếu truy vấn bọc cột trong hàm, ví dụ `WHERE
lower(email) = ...` sẽ không dùng index thường trên `email`; phải tạo
functional index trên `lower(email)`. Index cũng bị bỏ qua khi bảng quá nhỏ
hoặc khi truy vấn trả về phần lớn số dòng, lúc đó quét tuần tự lại nhanh hơn.
Dùng EXPLAIN ANALYZE để xem database có thực sự dùng index không.
