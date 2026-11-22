# Trạm điều phối thu gom rác

Ứng dụng demo cho môn Big Data. Gồm 60 khu, 3.600 hộ, 10.800 thùng và 180 xe nhỏ. Mỗi hộ có một thùng hữu cơ, một thùng tái chế và một thùng rác còn lại.

## Chạy trên Windows

Mở Docker Desktop ở chế độ Linux containers, rồi mở PowerShell tại thư mục này.

```powershell
docker compose up -d --build
docker compose ps
```

Mở [dashboard](http://localhost:8000) và bấm **Bật demo**. Lần đầu cần tải image và thư viện khi build. Sau khi các container lên, Spark vẫn cần thời gian để khởi tạo hai executor và nhận batch đầu tiên. Danh mục được nạp tự động. Phiên mới bắt đầu từ 30/10/2026 theo giờ Việt Nam.

```powershell
curl.exe -X POST http://localhost:8000/api/control/start
curl.exe -X POST http://localhost:8000/api/control/pause
curl.exe -X POST http://localhost:8000/api/control/stop
docker compose logs -f app stream
```

**Tạm dừng** và **Dừng** đều dừng phát sinh mới, giữ đồng hồ và dữ liệu. Các bản ghi đã đến hạn trong outbox tiếp tục được gửi và xử lý. Bật lại sẽ tiếp tục tại mốc đã lưu. Thoát xem log bằng Ctrl+C. Sau buổi demo, dùng `docker compose down` để giải phóng RAM và giữ các volume. Lần sau dùng `docker compose up -d`.

Các ô log nối dòng mới ở cuối và giữ tối đa 100 dòng gần nhất trên màn hình. Cuộn lên để đọc các dòng trước. Trang vận hành đếm lượt thu gom đã xử lý theo khu và loại rác, gồm các lượt gom xong hoặc gom một phần. Sự cố mất tín hiệu được giới hạn ở 19 thùng đang mất kết nối đồng thời.

Bộ mô phỏng gửi tối đa 550 bản ghi mỗi lô và giới hạn tốc độ gửi ở khoảng 1.100 bản ghi/giây thực. Hệ thống gửi hết các bản ghi đã đến hạn trong outbox trước khi sinh khung mới. Cảnh báo chờ Spark xuất hiện khi ít nhất 16.000 bản ghi đã vào Kafka còn chờ xử lý.

Các số đo từ những thùng khác nhau được gửi xen kẽ theo mức đầy nếu có nhiều mức. Terminal vận hành cũng xen kẽ dòng mới từ các thùng và xe khác nhau, giữ thứ tự của từng mã và hiển thị giờ phát sinh gốc.

## Kịch bản trình bày

| Trình tự | Thao tác | Điều cần quan sát |
| --- | --- | --- |
| 1 | Bật demo, vào **Cảnh báo & thu gom** và lọc khu 01 | Mức đầy thay đổi, xuất hiện điểm gom, log xe tới điểm và đổ ở trạm. |
| 2 | Chọn **Cao điểm 10.000 số đo**, sang **Sức khỏe hệ thống** | Dữ liệu dồn qua các partition, số task tăng ở hai executor, độ trễ và cách ly thay đổi. |
| 3 | Khi đã có điểm gom, chọn **Hỏng xe & mất tín hiệu** | Thùng H-0001-O mất tín hiệu, log ghi nhận sự cố xe nếu có tuyến phù hợp. Hàng trên xe hỏng được giữ lại và tuyến chưa thực hiện được mở lại. |
| 4 | Qua mốc 01/11, chọn tháng 10 ở **Hóa đơn & đối soát** | 3.600 hóa đơn, chi tiết kg theo loại và nút in. Kỳ 10 có hai ngày lịch sử mô phỏng. Lọc khu 01 để xem H-0004 gửi lại, H-0002 sai tiền và H-0020 chưa trả. |
| 5 | Qua mốc 01/12, lọc tháng 10 ở **Tài chính** và tháng 11 ở **Kế hoạch** | H-0020 quá hạn, H-0002 vẫn được phục vụ do giao dịch đúng hộ/đúng hóa đơn đang đối soát tiền. H-0001 trả trễ sau mốc ngưng. Kế hoạch tháng 11 hiện dung tích/tần suất trước và sau. |

Nên chạy trước đến mốc 01/12 nếu thời lượng thuyết trình ngắn, tạm dừng và giữ volume. Khi lên lớp, bật tiếp để minh họa luồng trực tiếp và xem lại các kỳ đã chốt. Đồng hồ tăng 12 giờ mô phỏng mỗi khung. Tốc độ thực phụ thuộc máy và hàng đợi, nhất là batch đầu và thời điểm chốt kỳ.

## Các điểm quan sát

- [Spark Master](http://localhost:8089) cho thấy hai worker. [Spark Driver UI](http://localhost:4040) có tab Executors và stages.
- [HDFS NameNode](http://localhost:9870) cho thấy hai DataNode. Dữ liệu nằm ở `/waste/batches/<batch>/layer=<raw|clean|quarantine|analysis>/day=...`. Checkpoint nằm ở `/waste/checkpoint`.
- [Swagger](http://localhost:8000/docs) mô tả API. [Kiểm kê](http://localhost:8000/api/audit) trả số tổng hợp để đối chiếu.
- Xem hướng dẫn [kiến trúc, công thức và nghiệm thu](docs/BAO_CAO.md).
- Xem [kết quả chạy thử trên máy này](docs/KET_QUA.md).

RAM thực tế thay đổi theo tải. Nên đóng ứng dụng nặng trên máy 16 GB trước khi chạy. Toàn bộ cổng giao diện chỉ mở ở localhost.

## Mã nguồn

| Đường dẫn | Vai trò |
| --- | --- |
| `compose.yaml`, `cluster/` | Cụm Docker, bản sao HDFS, cấu hình Spark và môi trường chạy |
| `src/simulation.py`, `src/runner.py` | Sinh dữ liệu, điều xe, đồng hồ, outbox và HTTP → Kafka |
| `src/stream.py` | Làm sạch và tổng hợp phân tán, Parquet, ghi kết quả theo batch |
| `src/finance.py`, `sql/001.sql` | Chốt phí, tạo kế hoạch, trạng thái nợ và cấu trúc PostgreSQL |
| `src/api.py`, `src/queries.py`, `web/` | API điều khiển, truy vấn dashboard và giao diện |

