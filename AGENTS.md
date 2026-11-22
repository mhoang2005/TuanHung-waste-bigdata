# Hướng dẫn AI tiếp tục dự án

## Bắt đầu
- Dự án hiện hành: `bigdata/`. Đọc README gốc, `bigdata/README.md`, `bigdata/docs/BAO_CAO.md`, rồi mã thực tế.
- Không lấy `project/` (VM/YARN) hoặc bản Streamlit từng tồn tại ở máy cũ làm nền. Người dùng đã bỏ bản đó. Thư mục ngoài repository `Documents/Giáo Trình/bigdata` không phải nguồn hiện hành và không được nhập lại tự động.
- Ngày bàn giao: 22/11/2026. Chỉ kiểm tra tệp và đóng gói Git; kết quả trong KET_QUA.md là ghi nhận trước đó, không phải kiểm thử mới.
- Nhóm 3 sinh viên, máy RAM 16 GB dùng chung với ứng dụng khác. Ưu tiên dễ hiểu, chạy ổn, vừa đủ chiều sâu Big Data, không thêm công nghệ chỉ để tăng số lượng.

## Yêu cầu giao diện đã chốt
Một thanh điều khiển Bật demo / Tạm dừng / Dừng dùng chung. Không bản đồ, không chọn nguồn dữ liệu. Năm trang: cảnh báo & thu gom; phân tích theo khu/hộ; kế hoạch kỳ tiếp theo; hóa đơn & đối soát; sức khỏe hệ thống. Bộ lọc giữ nguyên khi cập nhật/chuyển trang. Log nối dòng, giới hạn 100 dòng hiển thị, lịch sử vẫn lưu. Cột hộ chờ gom gồm khu, hộ, trạng thái thanh toán, tồn rác, cảnh báo; phải dùng tồn hiện tại, không dùng tổng phát sinh lịch sử hoặc loại vĩnh viễn nhà đã từng gom.

## Mã cần đọc
- `src/simulation.py`: hộ/thùng/xe, phát sinh và chuyển khối lượng.
- `src/runner.py`: đồng hồ 12 giờ/khung, outbox, điều khiển và tốc độ phát.
- `src/api.py`: API HTTP, điều khiển demo, API dashboard và hóa đơn.
- `src/stream.py`: Kafka, Spark, schema/chuẩn hóa, phân loại sạch/lỗi/trùng, HDFS, commit PostgreSQL.
- `src/finance.py`: chốt kỳ, hóa đơn, thanh toán, quá hạn, kế hoạch.
- `src/queries.py`, `src/db.py`, `sql/001.sql`: truy vấn và schema.
- `web/`: giao diện năm trang. `compose.yaml`, `cluster/`: cấu hình cụm.
Mọi đường dẫn trong mục này tương đối với bigdata/.

## Quy tắc cần bảo vệ
- Bảo toàn gram nguyên: phát sinh → tồn thùng → tải xe → trạm. Không cộng các số đo sensor thành lượng phát sinh.
- Mỗi sự kiện có ID; trùng/đến muộn không làm tăng khối lượng hoặc tiền lần hai; trạng thái không lùi về thời điểm cũ.
- Xe cùng khu/loại, tải giới hạn; hỏng giữ hàng, trả phần việc chưa làm về hàng chờ. Với chỉ một xe mỗi khu/loại có thể phải chờ xe hồi phục, không gọi đó là đã phân sang xe khác.
- Phí dựa kg đã thu từ từng hộ qua Spark; hóa đơn chụp giá và bất biến. Chờ đủ offset cuối kỳ rồi mới chốt.
- Thanh toán đủ tiền mới đóng hóa đơn. Gửi lại cùng mã/cùng nội dung, xung đột cùng mã, và mã khác trả hóa đơn đã trả là ba trường hợp khác nhau; giữ dữ liệu lỗi để đối soát.
- Hóa đơn tháng 10 phát hành 1/11, chưa trả đến 1/12 mới dừng gom. Sai tiền nhưng đúng hộ/hóa đơn đang đối soát vẫn phục vụ theo chính sách hiện hành. Không tự hoàn tiền.
- HDFS và PostgreSQL không có giao dịch nguyên tử chung; không tuyên bố exactly-once xuyên hệ thống khi chưa chứng minh.

## Khác biệt với yêu cầu trước khi xây lại
YEU_CAU_DU_AN_MOI.md là lịch sử yêu cầu, không phải mô tả chính xác mọi dòng code hiện tại. Bản hiện hành dùng FastAPI/web, HTTP trước Kafka, bốn partition/topic, khung 12 giờ bắt đầu 30/10/2026. Ngưỡng 75/95/100%; điều chỉnh dung tích 5 lít theo tháng, giới hạn 10–100 lít, khoảng gom 24–120 giờ. Yêu cầu cũ từng nói tăng/giảm số thùng 40 lít theo tuần: chưa đồng nhất, cần làm rõ nếu sửa nghiệp vụ này. Xe chỉ có đề xuất số lượng, chưa tự tăng đội xe. Phí hiện hành 15.000đ cơ bản và 750/250/1.100đ mỗi kg theo ba loại, khác mức giả định cũ. Không đổi âm thầm hoặc mô tả như đã thỏa cả hai phiên bản.

## Demo và xác minh trên máy mới
- Docker Compose mới tạo danh mục và volume; không có lịch sử của máy cũ đi kèm Git.
- Bật demo và chờ Spark khởi tạo; kiểm tra 5 trang, JSON API, hai executor, hai DataNode.
- Qua 1/11 có hóa đơn tháng 10 (chỉ hai ngày dữ liệu 30–31/10, phải ghi rõ). Qua 1/12 có kỳ tháng 11 hoàn chỉnh, kế hoạch và quá hạn tháng 10.
- Có kịch bản cao điểm 10.000 số đo/60 giây MÔ PHỎNG, không phải 10.000/s thực; có sự cố xe/mất tín hiệu.
- SQL nghiệm thu: `docs/audit.sql`; kiểm tra trình duyệt: `docs/browser-smoke.mjs`, cần Node và Chrome/Edge, xem README/BAO_CAO.
- Các script trong work/ có thể chứa đường dẫn tuyệt đối máy cũ: đọc trước, không chạy hàng loạt.
- Không xóa volume/checkpoint khi sửa lỗi nếu chưa có yêu cầu. Không đưa khóa/token/file môi trường lên Git. Không gọi hệ thống hoàn tất chỉ vì trang trả HTTP 200.

## Cách làm việc với người dùng
Nói tiếng Việt rõ ràng, báo đúng phần đã làm/đã kiểm tra. Người dùng không muốn nhiều xác nhận lặt vặt và không muốn dùng computer use; ưu tiên CLI, code, API. Khi cần thao tác giao diện thì hướng dẫn. Sửa đúng bài toán, không thêm AI/ML, bản đồ hoặc VM/YARN trở lại nếu chưa có yêu cầu mới.
