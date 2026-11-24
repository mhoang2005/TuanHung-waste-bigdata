# Trạm Điều Phối Rác Tuấn Hùng — Hệ thống Quản lý Thu gom & Tính phí Rác Hộ Gia Đình

Dự án xây dựng **Trạm Điều Phối Rác Tuấn Hùng** — hệ thống khép kín quản lý thu gom, quy hoạch thùng/đội xe tự động và tính phí rác theo hộ gia đình trên nền tảng **Apache Kafka, Spark Structured Streaming, Hadoop HDFS, PostgreSQL và FastAPI**.

## 1. Khởi chạy nhanh trên Windows

Chỉ cần nháy đúp vào file **`run-system.bat`** ở thư mục gốc, hoặc chạy bằng PowerShell:

```powershell
cd bigdata
docker compose up -d --build
```

Sau đó mở trình duyệt tại **http://localhost:8000**, bấm **▶ Bật demo** để chạy trực tiếp hoặc **↺ Đặt lại demo** để đưa toàn bộ dữ liệu (PostgreSQL · Kafka · HDFS) về mốc chuẩn ban đầu (`step = 70 · 00:00 04/12/2026`).

## 2. Vòng tròn Nghiệp vụ Khép kín (4 Bước + Nền tảng Big Data)

1. **Bước 1 — Cảm biến & Điều xe thu gom (Tab 01)**:
   - Quản lý **60 khu × 60 hộ = 3.600 hộ gia đình**, **10.800 thùng rác** (3 loại: Hữu cơ `O`, Tái chế `R`, Còn lại `C`) và **180–360 xe thu gom nhỏ**.
   - Hiển thị tỷ lệ % hộ cần gom / tổng số hộ, tỷ lệ thùng & hộ để quá lâu, tỷ lệ quá tải (`>100%`) và tỷ lệ hộ nợ quá hạn ngừng gom (`5%`).
   - Mặc định chế độ **`Theo dõi 30 thùng mẫu`** (hiển thị đồng thời 13 dòng, có nút chuyển sang **`Tất cả các thùng 10.800`**):
     - Tự động đẩy các thùng gặp sự cố (`📡 Cảm biến hỏng · Đang sửa`, `🔧 Xe ... đang sửa`) và thùng chưa gom lên đầu bảng theo mức độ cảnh báo (`Quá tải >100%` → `Đã đầy 95–100%` → `Gần đầy 75–94%` → `Để quá lâu`).
     - Thùng vừa được thu gom hiển thị hiệu ứng xanh ngọc **`✓ Vừa gom xong`** kèm mã xe rồi hạ xuống cuối bảng.
     - Trong **~35 giây đầu** khi bật demo, 2 trong 3 hộ nợ quá hạn trong bộ 30 thùng mẫu (`H-0120`, `H-0340`) lần lượt thanh toán bù hóa đơn và được mở khóa điều xe thu gom ngay, chỉ giữ lại 1 thùng nợ quá hạn cố định (`H-0020-O`) ở trạng thái **`⛔ Ngừng gom`**.
2. **Bước 2 — Thống kê & Biểu đồ trực quan (Tab 02)**:
   - Spark Structured Streaming tổng hợp khối lượng rác phát sinh và khối lượng thực tế đã thu gom theo ngày, khung giờ 24h, khu, hộ và loại rác.
   - Trang bị **5 biểu đồ tương tác (có tooltip chi tiết)**:
     1. Khối lượng phát sinh vs đã gom theo từng ngày trong tháng.
     2. Phân bố thu gom theo **24 khung giờ trong ngày** (cao điểm sáng `05–06h` & tối `17–20h` chiếm ~80%, rải rác các khung giờ thấp điểm chiếm ~20%).
     3. Top 15 khu dân cư có khối lượng thu gom lớn nhất.
     4. Cơ cấu 3 loại rác (Hữu cơ · Tái chế · Còn lại) và hiệu suất thu gom theo kỳ.
     5. Đối soát doanh thu phát hành vs thực thu theo từng tháng.
3. **Bước 3 — Tự động điều chỉnh Thùng rác, Lịch gom & Đội xe (Tab 03)**:
   - Cuối mỗi kỳ tháng, tự động **tăng/giảm dung tích thùng (±5 L, giới hạn 10–100 L)** và **rút ngắn/kéo dài lịch gom (±24 giờ, giới hạn 24–120 giờ)** cho từng hộ gia đình (có chốt chặn an toàn `blocked_capacity` nếu rác đang tồn vượt dung tích mới).
   - Tự động **tăng/giảm số lượng xe theo khu (1 ↔ 2 xe mỗi loại rác)** dựa trên mật độ lượt thu gom trong kỳ.
4. **Bước 4 — Hóa đơn, Đối soát Thanh toán & Kiểm soát nợ (Tab 04)**:
   - Tự động chốt sổ và phát hành **3.600 hóa đơn/tháng** (`15.000 đ phí cơ bản + Kg Hữu cơ × 750 đ + Kg Tái chế × 250 đ + Kg Còn lại × 1.100 đ`). Hỗ trợ xem và in PDF từng hóa đơn.
   - Hộ gia đình chuyển khoản kèm nội dung là **Mã hóa đơn**.
   - **Không thanh toán** hoặc **thanh toán thiếu tiền**: Sau 1 tháng kể từ ngày phát hành hóa đơn sẽ chuyển sang trạng thái **Quá hạn · Ngừng gom** $\rightarrow$ Quay lại Bước 1 xe rác sẽ **bỏ qua không thu gom**.
   - **Thanh toán thừa tiền / gửi sai mã**: Hóa đơn thừa tiền vẫn được tính hoàn tất thu gom; hộ dân liên hệ Phòng Đối Soát Tuấn Hùng bên ngoài hệ thống (`SĐT: 0392196240` / `doisoat@tuanhung.vn`) để hoàn tiền thừa.

## 3. Kiến trúc Big Data

`Bộ sinh dữ liệu (IoT, Xe, Ngân hàng) → Apache Kafka (2 Topic × 4 Partition) → Spark Structured Streaming (1 Master + 2 Workers / Executors) → Hadoop HDFS (2 DataNodes, Replication = 2, Parquet 4 lớp: raw / clean / quarantine / analysis) + PostgreSQL → FastAPI & Web Dashboard`

- **Dashboard chính**: http://localhost:8000
- **Spark Master UI**: http://localhost:8089
- **Spark Driver UI**: http://localhost:4040
- **HDFS NameNode UI**: http://localhost:9870
- **Tài liệu toàn bộ dự án (Nghiệp vụ, Kiến trúc, Demo 5 phút)**: [TAI_LIEU_TOAN_BO_DU_AN.md](TAI_LIEU_TOAN_BO_DU_AN.md)
