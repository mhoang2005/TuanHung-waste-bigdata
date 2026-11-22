# Rà soát Oracle Linux 10.2 cho Smart Waste Big Data

Ngày đối chiếu: **23/10/2026**.

## Kết luận

Oracle Linux 10.2 x86_64 là phương án có thể triển khai cho lab này. Các yêu cầu nền tảng được công bố của stack có thể đáp ứng bằng Python 3.12 và một bản JDK 17 được duy trì, cài riêng cho ứng dụng. Hai hạng mục cần thiết kế kỹ là môi trường Java của từng tiến trình và YARN trên cgroups v2.

Đã đối chiếu tài liệu chính thức, đọc thông tin host và tra metadata gói Python trên PyPI. **Chưa boot Oracle Linux 10.2, chưa chạy thử cụm và chưa xác nhận tích hợp đầu cuối.** Kết luận này là đánh giá điều kiện triển khai, không phải chứng nhận toàn bộ hệ thống đã hoạt động.

## 1. Host và VMware

Các giá trị sau được đọc trực tiếp từ Windows trong lần rà soát:

| Mục | Quan sát |
|---|---|
| VMware Workstation | 26.0.1 build-25688693 |
| CPU | Intel Core 7 150U, 10 core/12 logical processor |
| RAM hệ điều hành nhìn thấy | Khoảng 15,7 GiB |
| RAM trống tại thời điểm đọc | Khoảng 2,3 GiB |
| Dung lượng trống ổ C | Khoảng 566,6 GiB |
| VM đang chạy | 0 |

VMware đã bổ sung Oracle Linux 10 vào danh sách guest từ Workstation 25H2. Đây là bằng chứng hỗ trợ nhánh Oracle Linux 10, chưa thay thế việc boot bản 10.2 trên cấu hình VM thực tế. [Thông báo VMware](https://blogs.vmware.com/cloud-foundation/2025/10/14/vmware-workstation-fusion-25h2-embracing-calendar-versioning-and-new-features/)

Oracle Linux 10 x86_64 yêu cầu x86-64-v3, ít nhất hai CPU logic và tài liệu cài đặt nêu mức RAM 1,5 GB mỗi CPU logic. CPU vật lý có AVX2 theo Intel; cần xác nhận tập lệnh thực tế được VMware trình bày cho guest. [Yêu cầu Oracle](https://docs.oracle.com/en/operating-systems/oracle-linux/10/install/install-SystemRequirements.html), [thông số CPU Intel](https://www.intel.com/content/www/us/en/products/sku/236795/intel-core-7-processor-150u-12m-cache-up-to-5-40-ghz/specifications.html)

Nếu còn VM Fedora, có thể xem khả năng CPU trong chính guest bằng:

```bash
/lib64/ld-linux-x86-64.so.2 --help | grep x86-64-v
```

Cần có `x86-64-v3 (supported, searched)`. Kết quả này chưa được thu thập trong lượt rà soát.

## 2. Java — hạng mục cần điều chỉnh

- Oracle Linux 10 mặc định dùng OpenJDK 21. [Oracle](https://docs.oracle.com/en/operating-systems/oracle-linux/10/relnotes10.0/ol10-features-CompilersandDevTools.html)
- Hadoop 3.5.0 yêu cầu Java 17 cho server; client hỗ trợ 17/21. [Hadoop](https://hadoop.apache.org/docs/r3.5.0/)
- Spark 4.0.4 hỗ trợ Java 17/21, Scala 2.13 và Python 3.9+. [Spark](https://spark.apache.org/docs/4.0.4/)
- Kafka 4.1 hỗ trợ Java 17 và 21. [Kafka](https://kafka.apache.org/41/operations/java-version/)

Phương án: cài Eclipse Temurin JDK 17 Linux x64 từ nguồn chính thức, dùng bản vá còn được duy trì; cấu hình đường dẫn JDK riêng và `JAVA_HOME` cho Hadoop, Spark, Kafka, systemd services và môi trường tiến trình YARN. Bản archive là một cách cài được Adoptium hướng dẫn. [Adoptium](https://adoptium.net/installation/archives/)

Đây là lựa chọn triển khai đề xuất. Cần xác nhận `java -version` của đúng đường dẫn JDK và các tiến trình guest trước khi triển khai cụm. Không suy ra Java của service từ Java đang hiển thị trong một terminal khác.

Kết quả tìm kho `ol10_distro_builder` có một số gói Java 17 cũ; điều đó chưa chứng minh Java 17 nằm trong AppStream được duy trì của hệ thống. Hướng dẫn cài sẽ không mặc định dùng những gói build cũ này.

## 3. HDFS, YARN và Spark

| Thành phần dự kiến | Kết quả đối chiếu | Việc còn cần làm |
|---|---|---|
| HDFS 3.5.0 | Có thể đáp ứng môi trường Java/Linux | Xác nhận JDK, thư viện native, thư mục dữ liệu, phân giải tên và đường truyền DataNode |
| YARN 3.5.0 | Có hỗ trợ cgroups v2 trong tài liệu | Cấu hình ngân sách tài nguyên và, nếu cưỡng chế giới hạn ở mức kernel, LinuxContainerExecutor/quyền/delegation phù hợp |
| Spark 4.0.4 trên YARN | Đáp ứng Java/Python; Spark có chế độ YARN | Thống nhất thư viện Hadoop client, Python, JAR và classpath trên ba VM |
| Spark Streaming/Batch | Có thể giữ nguyên mô hình ứng dụng | Xác nhận đọc/ghi Kafka/HDFS/PostgreSQL, checkpoint và khôi phục bằng chạy thực tế |

Oracle Linux 10 chỉ cung cấp cgroups v2; cgroups v1 không còn sẵn. Hadoop 3.5 có thuộc tính `yarn.nodemanager.linux-container-executor.cgroups.v2.enabled`, mặc định false. Cấu hình v1 từ một hướng dẫn cũ không áp dụng nguyên trạng. [Oracle cgroups](https://docs.oracle.com/en/operating-systems/oracle-linux/10/boot/boot-Managing_Resources_Cgroups.html), [Hadoop cgroups](https://hadoop.apache.org/docs/r3.5.0/hadoop-yarn/hadoop-yarn-site/NodeManagerCgroups.html)

YARN có thể lập lịch theo ngân sách khai báo; việc cưỡng chế mức dùng CPU/RAM thực tế là một hạng mục cấu hình và đo riêng. Chưa có bằng chứng về cưỡng chế cgroups trên guest trong lượt này.

Spark phân biệt bản có Hadoop runtime và bản `no-hadoop`. Khi dùng Hadoop 3.5 cần chọn/cấu hình runtime nhất quán; tránh chồng nhiều bộ JAR Hadoop. [Spark trên YARN](https://spark.apache.org/docs/4.0.4/running-on-yarn.html)

Kiểm tra native cần làm sau khi cài:

```bash
hadoop checknative -a
```

Lệnh này kiểm tra nạp thư viện native. Kết quả từng codec cần được xem riêng; không thể kết luận mọi codec hoạt động chỉ từ phiên bản OS/Java. [Hadoop native libraries](https://hadoop.apache.org/docs/r3.5.0/hadoop-project-dist/hadoop-common/NativeLibraries.html)

## 4. Kafka và thư viện kết nối Spark

Kafka 4.1.2/KRaft có thể giữ trong thiết kế, dùng JDK 17 đã cấu hình. Thiết kế ba broker/controller, ba partition, RF=2 không cần đổi chỉ vì hệ điều hành.

Connector ứng với Spark 4.0.4 là:

```text
org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.4
```

Phiên bản connector đi theo Spark/Scala. Tài liệu tích hợp mô tả hỗ trợ Kafka broker 0.10 trở lên; vẫn cần chạy luồng thực tế với broker 4.1.2 và cấu hình dự án. [Spark Kafka integration](https://spark.apache.org/docs/4.0.4/streaming/structured-streaming-kafka-integration.html)

## 5. Python và các gói đang có trong dự án

Oracle Linux 10 dùng Python 3.12 mặc định, đáp ứng mức Python của Spark đã chọn. Dùng môi trường `venv` và cùng phiên bản Python cho Driver/executor. [Oracle Python](https://docs.oracle.com/en/operating-systems/oracle-linux/10/python/python-InstallingPython.html)

Đã đọc API metadata PyPI, không cài gói, cho đúng các phiên bản đang có trong `app/requirements.txt`:

| Gói | Yêu cầu Python | Gói được công bố phù hợp |
|---|---|---|
| confluent-kafka 2.12.2 | >=3.8 | CPython 3.12, Linux x86_64 manylinux_2_28 và Windows amd64 |
| psycopg 3.2.12 | >=3.8 | Python 3 wheel chung |
| psycopg-binary 3.2.12 | >=3.8 | CPython 3.12, Linux x86_64 manylinux2014/manylinux_2_17 và Windows amd64 |

Nguồn metadata: [confluent-kafka](https://pypi.org/pypi/confluent-kafka/2.12.2/json), [psycopg](https://pypi.org/pypi/psycopg/3.2.12/json), [psycopg-binary](https://pypi.org/pypi/psycopg-binary/3.2.12/json).

Oracle công bố glibc 2.39 trong bản cập nhật image 10.2; điều này phù hợp ngưỡng glibc của các wheel Linux trên. Đây là suy luận từ metadata/ABI nền, chưa phải kết quả import hoặc kết nối từ guest. [Oracle image 10.2](https://docs.oracle.com/en-us/iaas/images/oracle-linux-10x/oracle-linux-10-2-2026-09-18-0.htm)

Producer dự kiến chạy trên Windows nên không phụ thuộc trực tiếp OS của VM. Client này có binary wheels; psycopg cũng có tùy chọn binary tự chứa thư viện. [Confluent](https://docs.confluent.io/kafka-clients/python/current/overview.html), [Psycopg](https://www.psycopg.org/psycopg3/docs/basic/install.html)

## 6. PostgreSQL, dashboard và giám sát

| Thành phần | Vị trí dự kiến | Đánh giá |
|---|---|---|
| PostgreSQL 16.x | Windows host | Đổi OS guest không đổi nền tảng server; còn cấu hình kết nối từ guest |
| Grafana | Windows host | Có installer/binary Windows chính thức |
| Prometheus | Windows host | Thu metrics qua HTTP từ các endpoint trên VM |
| node_exporter | Ba VM Linux | Có các collector Linux cho CPU/RAM/disk/network; cần xác nhận quyền và endpoint thực tế |
| JMX Exporter | JVM của dịch vụ trên VM | Có chế độ Java agent; chọn bản hỗ trợ JDK 17 và cấu hình cho từng dịch vụ |
| Windows exporter | Windows host | Giữ vai trò giám sát host; độc lập OS guest |

Nguồn: [PostgreSQL Windows](https://www.postgresql.org/download/windows/), [Grafana Windows](https://grafana.com/docs/grafana/latest/setup-grafana/installation/windows/), [Prometheus](https://prometheus.io/docs/introduction/first_steps/), [node_exporter](https://github.com/prometheus/node_exporter), [JMX Exporter](https://prometheus.github.io/jmx_exporter/).

Nếu bổ sung ghi PostgreSQL bằng JDBC, nhánh pgJDBC 42.7 dùng được trên Java 8 trở lên, có thể dùng với JDK 17. Code hiện tại dùng psycopg trong `foreachBatch`, nên JDBC chưa phải dependency bắt buộc. [pgJDBC](https://jdbc.postgresql.org/download/)

## 7. Airflow — giai đoạn sau

Airflow 3.3.2 liệt kê Python 3.12 và PostgreSQL 16 trong bộ được kiểm thử; triển khai trên Linux, dùng venv riêng và constraints thích hợp. Bộ CI của Airflow dùng Debian, nên danh sách yêu cầu không phải chứng nhận riêng Oracle Linux 10.2. Tài liệu khuyến nghị tối thiểu 4 GB RAM tùy cách triển khai. [Airflow prerequisites](https://airflow.apache.org/docs/apache-airflow/stable/installation/prerequisites.html)

Spark provider 6.3.3 yêu cầu Airflow >=2.11.0 và có các dependency riêng. Khi cài cần khóa dependency cùng Spark 4.0.4, không để một lần cài provider vô tình thay bộ Spark của dự án. [Spark provider](https://airflow.apache.org/docs/apache-airflow-providers-apache-spark/stable/index.html)

Chưa cài Airflow vào ngân sách vận hành đồng thời của ba VM.

## 8. RAM, mạng và vận hành

- Khởi điểm thảo luận: VM1 4 GiB, VM2/VM3 mỗi máy 3 GiB, 2 vCPU/máy. 10 GiB guest cộng phần host/VMware và các dịch vụ là tải chật trên máy 16 GB.
- RAM trống 2,3 GiB hiện tại không đủ để bắt đầu chạy cả cụm theo cấu hình này; cần giảm workload khác trước.
- Đo tổng RAM tiến trình/JVM/OS và chừa memory overhead, ApplicationMaster, Driver; chưa thể chốt mỗi executor 1 GB chỉ từ lượng RAM gán cho VM.
- Ban đầu chạy Streaming/Batch luân phiên, Airflow để sau. Hệ điều hành mới không giải quyết thiếu RAM.
- Hostname/IP, đồng bộ giờ, SSH và các cổng dịch vụ cần được cấu hình. Host phải truy cập được địa chỉ Kafka quảng bá trên cả ba VM.
- Dùng systemd và cấu hình SELinux/firewalld phù hợp thư mục/cổng/quyền cần thiết. Hướng dẫn mạng của VM cũ phải đối chiếu lại tên NIC và IP sau khi cài OS mới.

## 9. Những xác nhận còn thiếu trước khi clone rộng

1. Boot VM1 Oracle Linux 10.2 với CPU/mạng/đĩa và gói guest tools hoạt động.
2. JDK 17 được duy trì chạy đúng; Python 3.12 và các gói cần thiết import được.
3. Thư viện Hadoop native và quyền thư mục hoạt động theo codec cần dùng.
4. Sau khi có ba VM: HDFS nhận đủ DataNode và YARN nhận đủ NodeManager.
5. Ứng dụng Spark thực sự chạy task trên ba guest; xác nhận vị trí executor và giới hạn tài nguyên.
6. Kafka -> Spark -> HDFS/PostgreSQL hoạt động; checkpoint, retry và bản sao được quan sát thực tế.

Các mục trên là phần cần làm trong giai đoạn cài đặt, chưa được thực thi trong lần rà soát phiên bản này.

## 10. Bộ cài nếu chọn Oracle Linux 10.2

```text
OracleLinux-R10-U2-x86_64-dvd.iso
```

Chọn x86_64 Full ISO trên [trang Oracle chính thức](https://yum.oracle.com/oracle-linux-isos.html); khi cài dùng môi trường không GUI. Tải ISO không đồng nghĩa cần cài toàn bộ các nhóm phần mềm trên DVD.
