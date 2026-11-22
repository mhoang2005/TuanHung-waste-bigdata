ĐỀ CƯƠNG TIỂU LUẬN DỮ LIỆU LỚN

1  Tên tiểu luận

Thiết kế và triển khai hệ thống Big Data phân tích dữ liệu rác thải đô thị theo hộ gia đình, khu vực và loại rác, hỗ trợ lập kế hoạch và giám sát thu gom sử dụng Apache Kafka, Spark và Hadoop HDFS

2  Giảng viên hướng dẫn

PGS. TS. Lê Hải Châu

PGS. TS. Nguyễn Chiến Trinh

3  Nhóm thực hiện

Nhóm 12



Họ và tên | Mã sinh viên | Lớp

--- | --- | ---

Đỗ Minh Hoàng | B23DCKD024 | D23CDKD02-B

Nguyễn Hải Đăng | B23DCKD010 | D23CDKD02-B

Chu Quốc Đạt | B23DCKD12 | D23CDKD02-B

Thành viên thứ tư | Chưa có thông tin | Chưa có thông tin

Thông tin ba thành viên và hai giảng viên được giữ theo đề cương trước. Nhóm cần bổ sung danh tính thành viên thứ tư và kiểm tra lại mã sinh viên của Chu Quốc Đạt trước khi nộp.

4  Bối cảnh và lý do chọn đề tài

Lượng rác sinh hoạt khác nhau giữa các hộ, các khu vực và các thời điểm. Trong một điểm gom, rác hữu cơ, rác tái chế và rác còn lại có sức chứa và yêu cầu thu gom khác nhau. Một lịch thu gom cố định có thể khiến xe đến khi lượng rác còn ít, trong khi điểm khác bị quá tải hoặc rác phải chờ quá lâu. Sự kiện tại một khu vực hoặc xe không sẵn sàng cũng có thể làm lịch thông thường không còn phù hợp.

Đề tài xây dựng môi trường mô phỏng để người quản lý theo dõi rác phát sinh, biết lượng đã thu gom và lượng còn tồn, đồng thời so sánh phương án điều chỉnh lịch với lịch cố định. Dữ liệu được sinh bằng Python theo quy luật và ràng buộc vật chất; thông tin cảm biến IoT là dữ liệu mô phỏng, không yêu cầu thiết bị thật.

Kafka, Spark và HDFS được sử dụng để tiếp nhận luồng sự kiện, xử lý dữ liệu song song và lưu lịch sử có bản sao. Giá trị của hệ thống được đánh giá đồng thời qua kết quả phục vụ thu gom và bằng chứng vận hành pipeline, thay vì chỉ dựa vào số lượng công nghệ triển khai.


---

4  Bối cảnh và lý do chọn đề tài

4 1  Phát biểu bài toán nghiệp vụ

Với số xe, tải trọng và thời gian làm việc hữu hạn, hệ thống cần hỗ trợ xác định điểm gom nào, loại rác nào cần được phục vụ, khoảng thời gian thu gom và thứ tự ghé các điểm. Mục tiêu là kiểm soát rác quá tải và quá hạn, đồng thời theo dõi quãng đường, số chuyến và mức sử dụng nguồn lực. Đề tài không giả định một phương án luôn tốt hơn trên mọi chỉ số.

4 2  Người sử dụng và đối tượng quản lý

Người sử dụng chính là cán bộ quản lý thu gom. Nhân viên hoặc đội thu gom là đối tượng được phân công công việc; hoạt động xe và xác nhận lấy rác được thực hiện bởi mô phỏng. Hộ gia đình là nguồn phát sinh dữ liệu, chưa có ứng dụng riêng để đăng ký hoặc thanh toán.

• Hộ gia đình thuộc một khu vực và giao rác đến một điểm gom cố định; dữ liệu ghi nhận số người, lượng phát sinh và cơ cấu loại rác.

• Mỗi điểm gom có ba ngăn độc lập; cần theo dõi tồn, sức chứa, lần gom gần nhất và thời gian chờ theo từng loại.

• Mỗi xe có đội phụ trách, loại rác phục vụ, tải trọng, vị trí, ca hoạt động và trạng thái công việc; trạm tiếp nhận có luồng tiếp nhận riêng theo loại.

4 3  Quy trình nghiệp vụ dự kiến

Rác phát sinh tại hộ và được giữ tạm thời. Đến khung giờ giao rác, khối lượng được chuyển đến ngăn tương ứng tại điểm gom. Hệ thống ghi nhận số đo, tổng hợp nhu cầu và xác định điểm đến hạn hoặc có nguy cơ quá tải. Xe nhận điểm đến, di chuyển theo đồ thị đường, bốc lượng phù hợp với tải còn trống và cập nhật phần đã lấy. Khi đầy hoặc kết thúc chuyến, xe về trạm dỡ rác. Lịch sử này được dùng để đề xuất tần suất cho kỳ tiếp theo và đánh giá chính sách.

4 4  Các tình huống cần giải quyết

• Một điểm có hữu cơ gần đầy nhưng tái chế còn ít: ưu tiên đúng luồng hữu cơ, không gộp ba loại thành một trạng thái đã gom.

• Xe không đủ chỗ lấy hết rác: xác nhận thu gom một phần, giữ lại lượng tồn và đưa phần chưa phục vụ vào đánh giá tiếp theo.

• Một khu có sự kiện được thông báo trước: bổ sung nhu cầu công cộng dự kiến để xem xét gom sớm; lượng rác này không tính vào mức phí của hộ.

• Cảm biến mất tín hiệu: cảnh báo dữ liệu cũ và dùng lịch dự phòng; rác vẫn tiếp tục phát sinh, không coi giá trị thiếu là bằng không.

• Khu thường xuyên quá tải hoặc được ghé khi còn ít rác: phân tích lịch sử để đề xuất tăng, giảm tần suất hoặc xem xét tăng sức chứa.


---

5  Mục đích và phạm vi của tiểu luận

5 1  Mục tiêu nghiên cứu và triển khai

• Làm rõ mối liên hệ giữa dữ liệu phát sinh từ hộ, tồn tại điểm gom, hoạt động xe và quyết định lập lịch theo khu vực và loại rác.

• Triển khai pipeline tiếp nhận, chuẩn hóa, kiểm tra, xử lý trùng và tổng hợp dữ liệu trên Kafka, Spark, HDFS và PostgreSQL.

• Xây dựng chính sách điều chỉnh lịch có giải thích, mô phỏng thực hiện thu gom và so sánh kết quả với lịch cố định trên cùng nhu cầu đầu vào.

• Trực quan diễn biến trên bản đồ giả lập, cung cấp thống kê hoạt động, đề xuất mức phí theo khu và cảnh báo sự cố dữ liệu hoặc hệ thống.

5 2  Phạm vi dữ liệu và môi trường

Cấu hình minh họa gồm 360 hộ thuộc 6 khu vực trong 3 quận, 12 điểm gom, 3 loại rác, 6 xe và 1 trạm tiếp nhận. Thời gian mô phỏng cơ sở là 14 ngày; quy mô có thể thay đổi bằng tham số số hộ và số ngày. Các trường thông tin về hộ, điểm gom, xe và sự kiện đều là dữ liệu tổng hợp, không phải hồ sơ dân cư thực.

Triển khai bằng Docker Compose trên một máy chủ vật lý 16 GB RAM, gồm Spark Standalone với hai Worker và HDFS với hai DataNode. Đề tài minh họa xử lý và lưu trữ phân tán giữa các tiến trình/container; không trình bày đây là cụm nhiều máy vật lý có khả năng chịu lỗi toàn máy.

5 3  Dữ liệu được sinh có quy luật

Mỗi hộ có hồ sơ ổn định gồm số người, hệ số sinh hoạt, cơ cấu ba loại rác và giờ giao rác. Lượng phát sinh theo ngày phụ thuộc quy mô hộ, đặc điểm khu, ngày thường hoặc cuối tuần và dao động nhỏ có seed. Tổng lượng rác được phân thành từng loại theo tỷ trọng cộng bằng 100%; chỉ chuyển ra điểm gom khi đến giờ giao.

Cần tách trạng thái thực của thế giới mô phỏng khỏi bản tin quan sát. Độ đầy được suy từ khối lượng và sức chứa, vị trí xe từ chặng đường đang đi; bản tin trùng, trễ, lỗi số đo hoặc mất tín hiệu được chèn có kiểm soát sau khi cập nhật trạng thái. Các tham số về kg/người/ngày, khối lượng riêng, vận tốc, thời hạn và tỷ trọng là giả định được công bố, chưa phải kết quả hiệu chuẩn thực địa.

Ràng buộc kiểm tra ở mỗi bước: tổng rác phát sinh bằng lượng còn tại hộ cộng tồn điểm gom, tải xe và tổng đã vào trạm. Lượng lấy bằng giá trị nhỏ hơn giữa tồn ngăn và tải xe còn trống. Rác vượt sức chứa vẫn được giữ lại để phản ánh quá tải; không tự cắt bỏ dữ liệu dư.


---

5 4  Các nội dung tính toán và hỗ trợ quyết định

• Tổng hợp lượng phát sinh, lượng giao, lượng đã gom và tồn theo hộ, khu vực, loại rác và thời gian. Không cộng số đo tồn cảm biến thành lượng phát sinh; không cộng lại lượng dỡ trạm vào lượng thu gom.

• Tính tốc độ phát sinh trung bình từ tối đa bảy ngày đã hoàn thành. Ước tính thời gian đến ngưỡng sức chứa từ lượng còn trống và tốc độ phát sinh; nếu thiếu lịch sử thì dùng lịch mặc định.

• Đề xuất khoảng gom trong tập lựa chọn hữu hạn, có xét sức chứa và thời gian chờ tối đa theo loại. Nếu chu kỳ tối thiểu vẫn không đáp ứng thì đề xuất xem xét nâng sức chứa; đề xuất cho khu và loại dựa trên nhu cầu các điểm trong khu.

• Chọn điểm tiếp theo bằng quy tắc ưu tiên và khoảng cách, đồng thời kiểm tra tải xe, ca làm việc và điểm đã được xe khác nhận. Dijkstra tìm đường ngắn cho từng chặng trên bản đồ giả lập; cách chọn nhiều điểm là heuristic, chưa khẳng định tối ưu tuyến toàn cục.

• Tính khối lượng phát sinh bình quân/hộ và bình quân/người theo khu. Đề xuất mức phí tham chiếu theo khu, điều chỉnh trong biên độ cấu hình theo kg/hộ so với toàn địa bàn; loại trừ rác sự kiện. Mức phí là giả định để phân tích, không phải biểu phí pháp lý hoặc hóa đơn thu tiền.

5 5  Phương pháp kiểm tra và đánh giá

Chạy hai phương án trên cùng hồ sơ hộ, nhu cầu phát sinh, đội xe, bản đồ và điều kiện sự cố. Ba ngày đầu sử dụng lịch cố định để tạo lịch sử; từ ngày thứ tư, phương án điều chỉnh chỉ được dùng thông tin đã xảy ra và lịch sự kiện có trước. Vệt di chuyển, lượng gom và tồn được mô phỏng lại theo từng phương án.



Nhóm chỉ số | Nội dung đánh giá

--- | ---

Mức phục vụ | Khối lượng gom đúng hạn, giờ ngăn có rác quá hạn, giờ quá tải và lượng tồn cuối kỳ.

Hoạt động xe | Quãng đường thực đi, số chuyến hoàn thành, số lượt ghé và lượt ghé không lấy được rác.

Thời gian | Thời gian rác chờ đến khi gom tính theo kg; thời gian chuyến xe được đo riêng.

Chất lượng dữ liệu | Số bản tin lỗi, trùng, muộn; đối soát ID và khối lượng với dữ liệu chuẩn của mô phỏng.

Vận hành Big Data | Thông lượng, thời gian micro-batch, độ trễ theo đồng hồ thực, tài nguyên và thời gian batch với một hoặc hai executor.

Kiểm tra phát lại dữ liệu không làm cộng đôi kết quả; khởi động lại Spark tiếp tục từ checkpoint; đọc được tệp HDFS khi một DataNode dừng và bản sao còn sẵn sàng. Đánh giá nhiều seed/kịch bản khi điều kiện cho phép. Giảm quãng đường phải được xem cùng mức phục vụ và tồn cuối kỳ, không đặt sẵn tỷ lệ cải thiện cần đạt.


---

6  Nội dung tiểu luận

CHƯƠNG I  TỔNG QUAN VỀ BIG DATA VÀ BÀI TOÁN RÁC THẢI ĐÔ THỊ

1.1. Tổng quan về dữ liệu lớn, dữ liệu theo luồng và dữ liệu lịch sử.
1.2. Xử lý song song, phân vùng dữ liệu và lưu trữ phân tán.
1.3. Bối cảnh quản lý rác từ hộ gia đình đến điểm gom và trạm tiếp nhận.
1.4. Người sử dụng, câu hỏi nghiệp vụ, thực thể và quy trình thu gom.
1.5. Mục tiêu, phạm vi, giả định dữ liệu mô phỏng và tiêu chí đánh giá.
1.6. Kết luận chương.

Chương I cần xác định hệ thống hỗ trợ quyết định gì, cho ai và dựa trên dữ liệu nào. Nội dung Big Data được liên hệ trực tiếp với nhu cầu xử lý lịch sử và sự kiện liên tục của bài toán.

CHƯƠNG II  PHÂN TÍCH THIẾT KẾ VÀ KIẾN TRÚC HỆ THỐNG

2.1. Yêu cầu chức năng và các ràng buộc phi chức năng của mô hình.
2.2. Thiết kế hộ dân, điểm gom, ngăn theo loại, đội xe, trạm và lịch sự kiện.
2.3. Thiết kế bộ sinh dữ liệu có quy luật và kiểm tra bảo toàn khối lượng.
2.4. Hợp đồng dữ liệu, khóa sự kiện, đơn vị đo và hai hệ thời gian.
2.5. Kiến trúc tổng thể, vai trò Kafka, Spark, HDFS và PostgreSQL.
2.6. Quy trình chuẩn hóa, kiểm tra, cách ly lỗi và chống cộng trùng.
2.7. Quy tắc lập lịch, đề xuất sức chứa, chọn điểm và đường di chuyển.
2.8. Chỉ số nghiệp vụ, mức phí mô phỏng, thiết kế map và cảnh báo.
2.9. Kết luận chương.

Chương II thể hiện quan hệ đầu vào – xử lý – đầu ra. Cần chỉ rõ phần mô phỏng và heuristic chạy bằng Python, phần xử lý dữ liệu phân tán chạy bằng Spark, cùng ranh giới giữa kho lịch sử và lớp phục vụ dashboard.

CHƯƠNG III  TRIỂN KHAI THỰC NGHIỆM VÀ ĐÁNH GIÁ

3.1. Môi trường Docker Compose, cấu hình tài nguyên và phiên bản dịch vụ.
3.2. Triển khai producer, topic và partition Kafka, Spark Master và Worker.
3.3. Triển khai HDFS, các lớp dữ liệu và checkpoint; PostgreSQL phục vụ.
3.4. Triển khai các chức năng nghiệp vụ, bản đồ và giám sát hệ thống.
3.5. Thực nghiệm thường ngày, sự kiện, mất tín hiệu và xe không sẵn sàng.
3.6. So sánh lịch cố định với lịch điều chỉnh trên cùng nhu cầu.
3.7. Đối soát pipeline, phát lại, kiểm tra bản sao và đo batch.
3.8. Nhận xét kết quả, đánh đổi, giới hạn và kết luận chương.

KẾT LUẬN: tổng hợp kết quả theo mục tiêu; chỉ ra điều đã kiểm chứng, điều còn hạn chế và hướng phát triển. Các bảng số liệu được lấy từ lần chạy có lưu cấu hình và bằng chứng, không thay kết quả thực bằng nhận định dự kiến.


---

7  Công nghệ dự kiến sử dụng



Công nghệ | Vai trò trong dự án và kiến thức vận dụng

--- | ---

Python | Sinh nhu cầu có seed; mô phỏng hộ, tồn và xe; heuristic lịch/điểm đến; producer và thí nghiệm đối chứng.

Apache Kafka | Tiếp nhận sự kiện; key theo điểm hoặc xe; partition, offset, lưu log và phát lại. Bản lab dùng một broker kiêm KRaft controller, RF bằng 1.

Apache Spark | Structured Streaming chuẩn hóa và kiểm tra dữ liệu, chống trùng có thời hạn, tổng hợp theo thời gian và thực thể; Spark SQL và batch lịch sử. Master và hai Worker quản lý executor, task và shuffle.

Hadoop HDFS | Lưu raw, clean, quarantine và dữ liệu tổng hợp dạng Parquet; lưu riêng checkpoint Spark. Một NameNode, hai DataNode; replication factor bằng 2 minh họa sao chép block.

PostgreSQL | Lưu danh mục, sự kiện hợp lệ, trạng thái hiện tại, tổng hợp, cảnh báo và lệnh điều khiển; dùng khóa sự kiện và giao dịch để hạn chế cộng trùng.

Streamlit và Plotly | Map mô phỏng, biểu đồ, bảng tra cứu, so sánh chính sách, mức phí và màn hình sức khỏe.

Docker Compose | Đóng gói dịch vụ, DNS mạng nội bộ, volume bền vững, hạn mức CPU/RAM và script triển khai có thể tái lập.

Luồng dữ liệu chính: Python → Kafka → Spark → HDFS và PostgreSQL → dashboard. Raw được giữ để truy vết; bản tin sai được cách ly; dữ liệu hợp lệ phục vụ thống kê và cập nhật trạng thái. Monitor đọc số liệu, kiểm tra thành phần và ghi cảnh báo hoặc báo cáo sức khỏe.

Phương án hiện tại dùng Spark Standalone thay YARN, phù hợp việc giảm chi phí triển khai trên một máy. Một giao diện Streamlit đảm nhiệm dashboard nghiệp vụ và sức khỏe cơ bản; Prometheus, Grafana và Airflow không thuộc phạm vi triển khai đã chọn. Không sử dụng ML hoặc LLM để dự báo hay phân loại bằng ảnh.

8  Ứng dụng của nội dung nghiên cứu

Đề tài cung cấp môi trường để thử lịch thu gom, quan sát điểm nghẽn và giải thích nguyên nhân một điểm bị quá tải hoặc chưa được phục vụ. Báo cáo theo hộ, khu và loại hỗ trợ xem xét tần suất, sức chứa và phương án phân bổ mức phí. Map cho phép đối chiếu xe đã đi đâu, đang mang loại rác nào và lượng tồn thay đổi sau khi lấy rác.

Về học phần, nhóm vận dụng phân vùng thông điệp, xử lý theo luồng và theo lô, task/executor, lưu trữ block có bản sao, checkpoint, chất lượng dữ liệu và khả năng tái xử lý. Dữ liệu mô phỏng và việc các container cùng chia sẻ phần cứng giới hạn khả năng suy rộng; kết quả là bằng chứng thực nghiệm của mô hình lab, chưa chứng minh hiệu quả kinh tế ngoài thực địa.


---

9  Tổ chức thực hiện và sản phẩm bàn giao

9 1  Nguyên tắc phân công

Nhóm tổ chức theo bốn mảng công việc, có người chịu trách nhiệm chính và người phối hợp kiểm tra đầu ra. Phân công dưới đây là phương án đề xuất để triển khai và bảo vệ; nhóm thống nhất lại trước khi ghi nhận đóng góp cuối kỳ. Danh tính vị trí thứ tư cần được bổ sung từ danh sách chính thức.

Đỗ Minh Hoàng phụ trách bài toán và mô phỏng nghiệp vụ

• Đặc tả hộ, khu, loại rác, điểm gom, đội xe và các tình huống; xây bộ sinh có seed, đồng hồ mô phỏng và cân bằng khối lượng.

• Triển khai hoặc hoàn thiện quy tắc lập lịch, ước tính đến đầy, đề xuất tần suất/sức chứa và heuristic chọn điểm, đường đi.

• Bàn giao: cấu hình mô phỏng, đặc tả nghiệp vụ, dữ liệu chuẩn, test bảo toàn và thiết kế so sánh hai chính sách; chủ trì phần bài toán ở Chương I và II.

Nguyễn Hải Đăng phụ trách thu nhận và chất lượng dữ liệu

• Thiết kế schema, khóa và đơn vị; producer Kafka, topic, partition, xác nhận gửi và replay log.

• Phối hợp xây luồng Spark chuẩn hóa, kiểm tra, cách ly lỗi, xử lý trùng và bản tin muộn; kiểm tra một sự kiện từ nguồn đến lớp hợp lệ.

• Bàn giao: hợp đồng dữ liệu, mã producer, kịch bản lỗi và replay, bảng đối soát ID/khối lượng; viết phần luồng dữ liệu và đánh giá chất lượng.

Chu Quốc Đạt phụ trách nền tảng xử lý và lưu trữ phân tán

• Thiết lập Docker Compose, Spark Master và hai Worker, HDFS NameNode và hai DataNode; cấu hình mạng, volume và tài nguyên.

• Hoàn thiện job stream/batch, checkpoint, các lớp Parquet; phối hợp thử restart, đọc bản sao và đo cùng tác vụ với một hoặc hai executor.

• Bàn giao: cấu hình và script triển khai, job xử lý, tài liệu vận hành và bằng chứng Spark/HDFS; chủ trì phần công nghệ và thực nghiệm hệ thống.

Thành viên thứ tư phụ trách lớp phục vụ và trực quan hóa

• Thiết kế PostgreSQL, cập nhật trạng thái và tổng hợp có chống cộng trùng; xây dashboard theo hộ/khu/loại, map xe và điểm gom.

• Triển khai màn hình lịch gom, báo cáo mức phí giả định, cảnh báo đầy/quá hạn/mất tín hiệu và sức khỏe thành phần.

• Bàn giao: lược đồ dữ liệu, dashboard/map, biểu đồ, báo cáo cảnh báo và kịch bản demo; phối hợp kiểm tra các công thức và trình bày kết quả.

Kiểm tra chéo: Hoàng với Đăng đối soát nguồn và dữ liệu hợp lệ; Đăng với Đạt kiểm tra replay/checkpoint; Đạt với thành viên thứ tư kiểm tra dữ liệu phục vụ; Hoàng với thành viên thứ tư đối chiếu chỉ số nghiệp vụ. Cả nhóm cùng chạy tích hợp, đọc log và giải thích giới hạn thí nghiệm.


---

9 2  Kế hoạch thực hiện trong tám tuần

Kế hoạch tính theo tuần công việc, điều chỉnh theo tiến độ môn học. Với phần đã có bản chạy, sử dụng thời gian tương ứng để rà soát, hoàn thiện và thu thập bằng chứng thay vì xây lại không cần thiết.



Tuần | Công việc chính | Điều kiện hoàn thành

--- | --- | ---

1 | Thống nhất bài toán, phạm vi, thực thể, chỉ số và phân công. | Đặc tả nghiệp vụ và hợp đồng dữ liệu được cả nhóm hiểu thống nhất.

2 | Hoàn thiện bộ sinh, ledger và kịch bản; kiểm tra seed và đơn vị. | Có dữ liệu mẫu và đối soát bảo toàn khối lượng.

3 | Dựng Compose, Kafka, Spark và HDFS; producer gửi dữ liệu. | Hai Worker và hai DataNode hoạt động; đọc được topic.

4 | Tích hợp chuẩn hóa, quarantine, chống trùng, Parquet và PostgreSQL. | Đối soát một bộ đầu vào với dữ liệu phục vụ và lịch sử.

5 | Hoàn thiện lịch, hoạt động xe, map và các báo cáo nghiệp vụ. | Demo đầy đủ một chu trình phát sinh – gom – dỡ trạm.

6 | Chạy baseline/adaptive, kịch bản sự kiện và sự cố có kiểm soát. | Có bảng so sánh cùng nhu cầu và giải thích các đánh đổi.

7 | Thử replay, restart, bản sao, đo batch và rà soát giao diện. | Lưu log, cấu hình và bằng chứng kiểm tra; sửa lỗi còn lại.

8 | Hoàn thiện báo cáo, slide, hướng dẫn và diễn tập bảo vệ. | Mỗi thành viên chạy, trình bày và trả lời được phần phụ trách.

9 3  Sản phẩm và tiêu chí bàn giao

• Một thư mục dự án chứa mã nguồn, cấu hình, lược đồ, script chạy/dừng và hướng dẫn; triển khai được trên môi trường phần cứng đã mô tả.

• Bộ dữ liệu có seed, config, dấu vết nguồn và dữ liệu chuẩn để đối soát; lịch sử raw/clean/quarantine/tổng hợp được tổ chức rõ ràng.

• Dashboard/map, cảnh báo và báo cáo so sánh có định nghĩa chỉ số; số liệu không cộng trùng và các giới hạn được công bố.

• Báo cáo tiểu luận, slide và bằng chứng thực nghiệm của cả nghiệp vụ lẫn Kafka, Spark, HDFS. Kết quả giảm đường đi không được diễn giải thành thành công nếu đi kèm bỏ sót hoặc tăng tồn mà chưa phân tích.

10  Tài liệu tham khảo

[1] Martin Kleppmann. Designing Data-Intensive Applications. O’Reilly Media, 2017.
[2] Apache Software Foundation. Apache Kafka Documentation. https://kafka.apache.org/41/
[3] Apache Software Foundation. Apache Spark Documentation. https://spark.apache.org/docs/4.0.4/
[4] Apache Software Foundation. Apache Hadoop Documentation. https://hadoop.apache.org/docs/r3.5.0/
[5] Docker. Docker Compose Documentation. https://docs.docker.com/compose/
