# Smart Waste Big Data

Dự án sinh dữ liệu IoT giả lập về rác thải, truyền qua Kafka, xử lý bằng Spark trên YARN, lưu lịch sử trên HDFS và phục vụ dashboard qua PostgreSQL/Grafana.

## Bắt đầu

Thực hiện [Bước 1: mở VM và xác nhận mạng/đăng nhập](docs/01-vm-va-mang.md). Chỉ bắt đầu với VM1; sau khi nắm được tình trạng thực tế mới tiếp tục VM2/VM3 và cài các dịch vụ.

## Trạng thái được quan sát ngày 22/10/2026

- Có các file VM dự án tại `C:\Users\OS\Documents\WasteLabVMs\vm1`, `vm2`, `vm3`.
- Chưa có VM đang chạy trong kết quả `vmrun list`. Chưa xác nhận hệ điều hành hay dịch vụ bên trong guest.
- Theo file cấu hình: VM1 có 3 GiB RAM; VM2/VM3 mỗi máy 2,5 GiB; cả ba có 2 vCPU/máy. Đây là cấu hình đã có, chưa phải ngân sách tài nguyên đã được xác nhận đủ cho toàn bộ stack.
- Host có khoảng 15,7 GiB RAM khả dụng cho hệ điều hành; tại lần đọc chỉ còn khoảng 2,3 GiB trống. Cần giảm tải ứng dụng khác trước khi bật VM.
- VMware NAT VMnet8 dùng mạng `192.168.200.0/24`, host `.1`, gateway/DNS `.2`. Các seed đã khai báo VM1 `.11`, VM2 `.12`, VM3 `.13`; địa chỉ trong guest chưa được xác nhận.
- Đã có code ứng dụng và schema PostgreSQL. Chưa có bằng chứng trong lần kiểm tra này rằng chúng đã chạy tích hợp trên cụm.

## Các chặng triển khai

| Chặng | Nội dung | Kết quả cần đạt |
|---|---|---|
| 1 | VM, mạng, SSH | Đăng nhập được từng guest, thống nhất hostname/IP |
| 2 | Java và HDFS | Một NameNode, ba DataNode, lưu block với RF=2 |
| 3 | YARN | Một ResourceManager nhận ba NodeManager; xác định ngân sách tài nguyên |
| 4 | Spark trên YARN | Chạy ứng dụng phân tán, quan sát vị trí executor thực tế |
| 5 | Kafka KRaft | Ba broker/controller, topic `waste-events`, ba partition, RF=2 |
| 6 | Luồng dữ liệu | Producer -> Spark Streaming -> HDFS; raw/clean/quarantine và checkpoint |
| 7 | Phục vụ kết quả | PostgreSQL, Grafana, Prometheus và các nguồn metrics |
| 8 | Phân tích lịch sử | Spark Batch tổng hợp và so sánh dung tích/lịch thu gom |

Airflow được bổ sung sau khi các chương trình batch đã có thể chạy độc lập. Bản đầu chưa dùng ML.

## Bố trí đích

| Máy | Các thành phần dự kiến |
|---|---|
| Host Windows | Python producer, PostgreSQL, Prometheus, Grafana |
| VM1 | Kafka broker/controller 1, NameNode/DataNode, ResourceManager/NodeManager, Spark Streaming Driver |
| VM2 | Kafka broker/controller 2, DataNode, NodeManager |
| VM3 | Kafka broker/controller 3, DataNode, NodeManager |

Executor được YARN khởi chạy cho từng ứng dụng. Mục tiêu ban đầu là ba executor, mỗi VM một executor; số lượng bằng ba chưa tự bảo đảm vị trí này. Ngân sách còn phải chừa chỗ cho ApplicationMaster, Driver, bộ nhớ phụ trợ, các dịch vụ khác và hệ điều hành.

## Code đã có

- `app/generate.py`: sinh dữ liệu NDJSON, danh mục và số liệu gốc để đối chiếu, dùng seed lặp lại được.
- `app/producer.py`: đọc NDJSON và phát vào Kafka theo key `bin_id`. Prototype này dùng file để phát lại dữ liệu; chưa phải chế độ sinh/gửi trực tiếp.
- `app/streaming.py`: bản nháp Spark Structured Streaming, lưu HDFS và cập nhật PostgreSQL.
- `database/schema.sql`: các bảng danh mục, trạng thái, cảnh báo và kết quả.
- `observability/`: các bản nháp thu thập tình trạng hệ thống và cấu hình metrics.
- `infra/create_vms.py`: script đã dùng để chuẩn bị file VM, có đường dẫn và thông số cố định; không phải lệnh cài cụm có thể chạy lại tùy ý.

Producer hiện mặc định dải `192.168.180.x`, còn Streaming dùng `192.168.200.x`. Khi tới chặng Kafka cần thống nhất bằng cấu hình chung hoặc tham số dòng lệnh. Chưa thay đổi code ứng dụng trong bước chuẩn bị hướng dẫn này.

## Nguyên tắc dữ liệu

- Sensor là ảnh chụp lượng rác đang có; không cộng các lần đo khối lượng thành tổng lượng rác phát sinh.
- Kafka replication và HDFS replication là hai cơ chế riêng. Cả hai dự kiến RF=2.
- Một NameNode, một ResourceManager và một Streaming Driver chưa tạo HA cho toàn bộ pipeline; ba VM vẫn cùng một host vật lý.
- Không công bố xử lý exactly-once xuyên HDFS/PostgreSQL khi chưa có cơ chế và bằng chứng tương ứng.

## Tài liệu nền

- [Hadoop Cluster Setup 3.5.0](https://hadoop.apache.org/docs/r3.5.0/hadoop-project-dist/hadoop-common/ClusterSetup.html)
- [Spark 4.0.4 trên YARN](https://spark.apache.org/docs/4.0.4/running-on-yarn.html)
- [Kafka KRaft 4.1](https://kafka.apache.org/41/operations/kraft/)

Các liên kết là tài liệu tham chiếu cho thiết kế; hướng dẫn cài từng dịch vụ và cấu hình phiên bản sẽ được chuẩn bị theo từng chặng sau khi guest đã hoạt động.
