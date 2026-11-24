# Trạm Điều Phối Rác Tuấn Hùng — Hệ thống Quản lý Thu gom & Tính phí Rác Hộ Gia Đình

Dự án xây dựng **Trạm Điều Phối Rác Tuấn Hùng** — hệ thống khép kín quản lý thu gom, quy hoạch thùng/đội xe tự động và tính phí rác theo hộ gia đình trên nền tảng **Apache Kafka, Spark Structured Streaming, Hadoop HDFS, PostgreSQL và FastAPI**.

## 1. Khởi chạy nhanh trên Windows

Chỉ cần nháy đúp vào file **`run-system.bat`** ở thư mục gốc, hoặc chạy bằng PowerShell:

```powershell
cd bigdata
docker compose up -d --build
```

Sau đó mở trình duyệt tại **http://localhost:8000** và bấm **▶ Bật demo**.

## 2. Vòng tròn Nghiệp vụ Khép kín (4 Bước + Nền tảng Big Data)

1. **Bước 1 — Cảm biến & Điều xe thu gom**:
   - Quản lý **60 khu × 60 hộ = 3.600 hộ gia đình**, **10.800 thùng rác** (3 loại: Hữu cơ `O`, Tái chế `R`, Còn lại `C`) và **180–360 xe thu gom nhỏ**.
   - Cảm biến tại từng thùng gửi khối lượng rác (`g` hoặc `kg`), quy đổi ra **% thể tích đầy** (`Gần đầy 75–94%`, `Đã đầy 95–100%`, `Quá tải >100%`) và cảnh báo `Để quá lâu`.
   - Hệ thống chấm điểm ưu tiên và phân xe cùng khu, cùng loại đi gom theo lộ trình ngắn nhất; xử lý sự cố xe hỏng và mất tín hiệu IoT.
2. **Bước 2 — Thống kê & Trực quan hóa khối lượng**:
   - Spark Structured Streaming tổng hợp khối lượng rác phát sinh và khối lượng thực tế đã thu gom theo ngày, khu, hộ và loại rác.
3. **Bước 3 — Tự động điều chỉnh Thùng rác, Lịch gom & Đội xe**:
   - Cuối mỗi kỳ tháng, tự động **tăng/giảm dung tích thùng (±5 L, giới hạn 10–100 L)** và **rút ngắn/kéo dài lịch gom (±24 giờ, giới hạn 24–120 giờ)** cho từng hộ gia đình.
   - Tự động **tăng/giảm số lượng xe theo khu (1 ↔ 2 xe mỗi loại rác)** dựa trên mật độ lượt thu gom trong kỳ.
4. **Bước 4 — Hóa đơn, Đối soát Thanh toán & Kiểm soát nợ**:
   - Tự động chốt sổ và phát hành **3.600 hóa đơn/tháng** (`15.000 đ phí cơ bản + Kg Hữu cơ × 750 đ + Kg Tái chế × 250 đ + Kg Còn lại × 1.100 đ`). Hỗ trợ xem và in PDF từng hóa đơn.
   - Hộ gia đình chuyển khoản kèm nội dung là **Mã hóa đơn**.
   - **Không thanh toán** hoặc **thanh toán thiếu tiền**: Sau 1 tháng kể từ ngày phát hành hóa đơn sẽ chuyển sang trạng thái **Quá hạn · Ngừng gom** $\rightarrow$ Quay lại Bước 1 xe rác sẽ **bỏ qua không thu gom**.
   - **Thanh toán thừa tiền / gửi sai mã**: Hóa đơn thừa tiền vẫn được tính hoàn tất thu gom; hộ dân liên hệ Phòng Đối Soát Tuấn Hùng bên ngoài hệ thống (`Hotline: 1900 6886` / `doisoat@tuanhung.vn`) để hoàn tiền thừa.

## 3. Kiến trúc Big Data

`Bộ sinh dữ liệu (IoT, Xe, Ngân hàng) → Apache Kafka (2 Topic × 4 Partition) → Spark Structured Streaming (1 Master + 2 Workers / Executors) → Hadoop HDFS (2 DataNodes, Replication = 2, Parquet 4 lớp: raw / clean / quarantine / analysis) + PostgreSQL → FastAPI & Web Dashboard`

- **Dashboard chính**: http://localhost:8000
- **Spark Master UI**: http://localhost:8089
- **Spark Driver UI**: http://localhost:4040
- **HDFS NameNode UI**: http://localhost:9870
- **Tài liệu toàn bộ dự án (Nghiệp vụ, Kiến trúc, Demo 5 phút)**: [TAI_LIEU_TOAN_BO_DU_AN.md](TAI_LIEU_TOAN_BO_DU_AN.md)
