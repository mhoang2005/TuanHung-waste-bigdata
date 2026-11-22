# Yêu cầu xây dựng lại dự án Big Data quản lý thu gom và thu phí rác thải

Hãy xây dựng mới từ đầu, thiết kế đơn giản, logic nghiệp vụ rõ ràng, không tái sử dụng bản triển khai cũ. Nhóm 3 sinh viên năm cuối, thời gian khoảng 2 tháng. Máy Windows RAM 16 GB còn dùng cho công việc khác. Dùng Docker Compose thay cho 3 máy ảo. Toàn bộ mã nguồn dự án mới đặt trong một thư mục bigdata. Không dùng computer use; thao tác giao diện cần thiết thì hướng dẫn người dùng.

## Mục tiêu
Theo dõi rác từng hộ, từng khu, từng loại; xác định nhu cầu thu gom; điều phối xe; tự điều chỉnh số thùng và tần suất thu gom theo lịch sử; tính phí từng hộ, phát hành hóa đơn, ghi nhận thanh toán và quản lý quá hạn. Không dùng AI/ML. Không làm bản đồ.

## Quy mô và dữ liệu
- 60 khu, mỗi khu 60 hộ, tổng 3.600 hộ. Mỗi hộ có mã riêng, số người, khu và điểm thu gom trước nhà.
- Ba loại rác: hữu cơ, tái chế, còn lại. Mỗi hộ có thùng riêng theo loại.
- Python sinh dữ liệu có quy luật: số người, loại rác, giờ phát sinh, khác biệt khu/hộ, ngày thường/cuối tuần, sự kiện báo trước. Có ngẫu nhiên nhỏ với seed tái lập được. Khối lượng phát sinh, tồn thùng, gom lên xe, đổ tại trạm phải bảo toàn.
- Dữ liệu xe: vị trí hoặc đoạn đường logic, trạng thái, tải trọng, nhiệm vụ, đến nhà, gom xong, về trạm, đổ rác, hỏng, hồi phục. Không cần trực quan bản đồ.
- Có dữ liệu lỗi có kiểm soát: thiếu/sai trường, sai đơn vị, trùng sự kiện, đến muộn, mất tín hiệu cảm biến; giữ bản gốc và tách bản lỗi.
- Luồng thanh toán riêng phát dựa trên hóa đơn thật đã được tính trong hệ thống.
- Mục tiêu tải cao điểm từng thảo luận: 10.000 bản ghi trong một phút mô phỏng. Phải chốt rõ đơn vị và đo kết quả thật. Con số 794.000 bản ghi/14 ngày thuộc cấu hình cũ, không dùng làm kết quả cho cấu hình mới.

## Nghiệp vụ
1. Theo dõi tồn hiện tại từng thùng, tỷ lệ đầy, thời gian chưa gom và mất tín hiệu. Cảnh báo gần đầy/quá tải/quá lâu. Phân biệt cần gom, đã phân xe, đang gom, gom một phần, gom xong. Nhà đã từng gom vẫn phải trở lại danh sách khi có nhu cầu mới.
2. Phân xe theo loại rác phù hợp, xe còn hoạt động, tải còn lại, độ khẩn cấp và khoảng cách. Dùng quy tắc ưu tiên và đường đi ngắn nhất đơn giản; không tuyên bố tối ưu toàn cục. Xe đầy phải về trạm. Xe hỏng giữ nguyên hàng đã gom; phân lại phần việc chưa làm cho xe phù hợp, không có xe thì để chờ và cảnh báo. Chốt phạm vi hỗ trợ giữa khu trước khi triển khai.
3. Phân tích khối lượng phát sinh/thu gom/tồn theo khu, hộ, loại, thời gian; thời gian chờ, số chuyến, quãng đường, mức sử dụng tải xe và thời gian hỏng.
4. Tự điều chỉnh số thùng và tần suất theo dữ liệu lịch sử đã hoàn thành. Có giới hạn và chu kỳ điều chỉnh; không giảm thùng nếu không đủ chứa rác tồn. Hiển thị lý do, trước/sau, hiệu lực và kết quả áp dụng. Phân biệt dự kiến tháng sau với quyết định đã thực hiện. Chưa chốt tự tăng số xe; không tự nhận đã có tính năng đó.
5. Phí theo từng hộ = phí cơ bản + kg thực tế đã thu từ hộ × đơn giá loại rác. Không tính trùng rác công cộng, không dùng tổng phát sinh thay cho lượng đã thu. Đơn giá là giả định mô phỏng, cần cấu hình được. Chốt hóa đơn tháng bất biến, có mã, kỳ, hộ, chi tiết và tổng tiền; xuất để xem/in.
6. Hộ trả toàn bộ hóa đơn, không thanh toán từng phần. Chuẩn hóa tiền, thời gian, mã hộ/hóa đơn/giao dịch. Cùng mã giao dịch và cùng nội dung là gửi lại: không cộng tiền lần hai. Cùng mã nhưng khác nội dung: xung đột. Hai mã giao dịch khác nhau cùng thanh toán một hóa đơn: khoản sau cần đối soát, không coi đơn thuần là trùng mã. Sai số tiền, sai hộ, sai hóa đơn, không tìm thấy hóa đơn phải giữ bản ghi và đánh dấu, không đánh dấu đã trả. Không tự hoàn tiền.
7. Hóa đơn tháng 10 phát hành 1/11: tháng 11 vẫn gom; chưa trả đến 1/12 mới dừng. Trả hết nợ quá hạn thì phục vụ lại. Giao dịch đang đối soát cần chính sách rõ ràng, bản thống nhất trước là vẫn phục vụ. Chờ luồng thanh toán xử lý xong trước khi xét dừng, tránh dừng sai do pipeline chậm.

## Công nghệ định hướng
Python → Kafka → Spark Structured Streaming → HDFS + PostgreSQL → dashboard.
- Kafka: hàng đợi sự kiện, topic thu gom và thanh toán riêng, partition theo khóa ổn định. Bản tối giản có thể 1 broker, không tuyên bố Kafka HA.
- Spark Standalone: master + 2 worker/executor để thể hiện xử lý song song. Không YARN. Spark làm sạch, chuẩn hóa, loại trùng, tổng hợp theo cửa sổ/kỳ, phân tích lượng rác/xe và tính kế hoạch, khối lượng tính phí.
- HDFS: NameNode + 2 DataNode, replication 2; giữ raw, clean, quarantine và kết quả phân tích. Hai bản sao trong cùng host không bảo vệ khi host hỏng.
- PostgreSQL: trạng thái phục vụ dashboard, nhiệm vụ, hóa đơn, thanh toán; khóa giao dịch và ràng buộc duy nhất bảo đảm không ghi nhận tiền hai lần.
- Python thực hiện mô phỏng/điều phối và áp dụng quyết định. Không phân executor theo nghiệp vụ; executor chạy task trên các phần dữ liệu.
- Batch tuần/tháng chỉ chạy khi dữ liệu kỳ đã đủ. Không cần Airflow cho phiên bản đầu.
- Dashboard có thể Streamlit hoặc lựa chọn phù hợp sau khi đánh giá khả năng cập nhật ổn định. Bản cũ dùng Streamlit nhưng giao diện và luồng điều khiển chưa đạt, không lấy làm mẫu.

## Dashboard yêu cầu chính xác
Không bản đồ, không chọn nguồn dữ liệu. Một thanh điều khiển ở phía trên dùng chung tất cả trang: BẬT DEMO, TẠM DỪNG, DỪNG. Bấm bật thì nguồn phát liên tục, tự bám lần chạy mới, bấm lại không tạo phiên trùng; chuyển trang không làm dừng nguồn. Cập nhật nội dung tại chỗ, không tải lại toàn trang hay mất bộ lọc.
1. Cảnh báo & thu gom: trên cùng là lượng rác, số nhà cần gom, số xe; dưới là ô log tín hiệu từng thùng, mức cảnh báo, nhà cần gom/đã gom; tiếp là danh sách gồm khu, hộ, trạng thái thanh toán, rác cần gom, mức cảnh báo. Có lọc khu, loại và xem lỗi xe/mất tín hiệu. Dùng tồn hiện tại, không cộng toàn lịch sử để suy ra tồn.
2. Phân tích: biểu đồ khối lượng từng khu, từng hộ, từng loại theo ngày/tháng; phát sinh và thu gom riêng; bộ lọc phù hợp, không chỉ bảng JSON.
3. Điều phối/kế hoạch: số thùng/sức chứa và tần suất hiện tại, quyết định tăng giảm, lý do, hiệu lực, kết quả; dự kiến tháng sau và hiệu quả xe.
4. Tài chính: ô log giao dịch và kết quả đối soát; số hộ đã/chưa đóng; danh sách trạng thái thanh toán lọc khu và tháng/năm; phía dưới danh sách số tiền phải đóng từng hộ với cùng bộ lọc; xuất hóa đơn. Log sai thông tin vẫn phải nhìn được.
5. Sức khỏe: trạng thái từng thành phần, độ trễ/tiến độ xử lý, log sự kiện/cảnh báo/lỗi và báo cáo sự cố. Phân biệt idle/paused/waiting với lỗi. Log trình duyệt có thể chỉ hiển thị 100 dòng gần nhất, lịch sử vẫn lưu.

## Demo và nghiệm thu
- Cần kịch bản demo dễ trình bày cho cả thu gom, kế hoạch và tài chính trong thời lượng hợp lý. Chốt cách tăng tốc thời gian hoặc nạp lịch sử hợp lệ; không bắt người xem chờ một tháng dữ liệu mới thấy tiền, không tạo hóa đơn giả không có cơ sở.
- Viết hướng dẫn khởi động từ Docker đã bật, thao tác một nút và cách dừng.
- Kiểm tra dữ liệu chạy thật qua Kafka/Spark/HDFS/DB; đối soát số lượng, tiền, tồn; thử trùng thanh toán, lỗi xe, mất tín hiệu và nợ qua tháng. Kiểm tra UI bằng dữ liệu thực đang chảy, bộ lọc giữ nguyên.
- Tối ưu RAM phù hợp host 16 GB; thử tải rồi mới báo số liệu hiệu năng, không gọi 10.000 bản ghi/phút mô phỏng là 10.000 bản ghi/giây thực.
- Triển khai từng phần hoàn chỉnh và kiểm tra, không chỉ đổi tên trang, placeholder trạng thái thanh toán hoặc tuyên bố đã làm khi chưa có.
