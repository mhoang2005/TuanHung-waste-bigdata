# Waste Big Data — bàn giao phát triển

Dự án bài tập lớn quản lý thu gom và thu phí rác theo hộ gia đình. **Mã nguồn hiện hành nằm trong `bigdata/`.** Đọc `AGENTS.md` trước khi giao việc cho AI.

## Chạy trên máy khác

Cài Git và Docker Desktop (Linux containers; Windows dùng WSL2). Clone repository này, sau đó:

```sh
cd bigdata
docker compose up -d --build
```

Mở http://localhost:8000 và bấm **Bật demo**. Một nút dùng chung năm dashboard, không chọn nguồn dữ liệu, không có bản đồ. Lần đầu Spark cần thời gian khởi tạo. Tạm dừng/tiếp tục giữ đồng hồ; dữ liệu đã vào hàng đợi tiếp tục xử lý.

```sh
docker compose ps
docker compose logs -f app stream
docker compose down
```

`down` giữ volume; không dùng `down -v` nếu cần giữ phiên demo. Git chỉ chuyển mã và tài liệu, không chuyển PostgreSQL, Kafka, HDFS hay checkpoint đang nằm trong Docker volume. Máy mới tạo dữ liệu mới. Không chạy đồng thời nhiều bản Compose của dự án trên cùng các cổng.

## Bài toán

60 khu × 60 hộ = 3.600 hộ; 10.800 thùng theo ba loại hữu cơ/tái chế/còn lại; 180 xe nhỏ. Theo dõi tồn thùng, mức đầy và tuổi chờ; phân xe phù hợp loại và khu, xử lý xe hỏng; thống kê khối lượng từng hộ/khu; điều chỉnh sức chứa và khoảng thu gom; chốt hóa đơn từng hộ và đối soát thanh toán. Quá hạn hết tháng kế tiếp mới ngừng phục vụ. Không AI/ML.

Python sinh sự kiện → outbox PostgreSQL → HTTP API → Kafka (2 topic, 4 partition/topic) → Spark Structured Streaming (2 worker/executor) → HDFS (2 DataNode, replication 2) + PostgreSQL → FastAPI và dashboard HTML/CSS/JavaScript. Một broker Kafka; không YARN; không tuyên bố HA khi hỏng host.

## Đọc tiếp

- [Hướng dẫn chạy và demo hiện hành](bigdata/README.md)
- [Kiến trúc, công thức, chính sách và nghiệm thu](bigdata/docs/BAO_CAO.md)
- [Kết quả được ghi nhận ngày 10/11/2026](bigdata/docs/KET_QUA.md): dữ liệu lịch sử, chưa tái chạy trong lần bàn giao 22/11/2026.
- [Ngữ cảnh và công việc cho AI](AGENTS.md)
- [Yêu cầu trước lần xây dựng lại](YEU_CAU_DU_AN_MOI.md): tham khảo ý định người dùng; một số công thức/tham số khác triển khai mới, xem AGENTS.md.

## Phân biệt các thư mục

| Thư mục | Vai trò |
| --- | --- |
| `bigdata/` | Dự án Docker/FastAPI hiện hành, ưu tiên phát triển tại đây |
| `project/` | Bản nháp cũ VM/YARN/Grafana, giữ để tham khảo, không chạy theo hướng dẫn này |
| `outputs/` | Đề cương cũ, cần cập nhật trước khi nộp theo phiên bản hiện hành |
| `work/` | Script và tài liệu làm việc lịch sử, có đường dẫn máy cũ; không phải lệnh cài dự án |

Không đưa khóa SSH, file `.env`, bộ cài, môi trường Python, ảnh máy ảo và dữ liệu sinh lớn vào Git. Mật khẩu `waste_demo` trong Compose là giá trị cố định dành cho lab cục bộ, không phải bí mật tài khoản thực; không dùng cấu hình này triển khai Internet.
