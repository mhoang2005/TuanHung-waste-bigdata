# Kết quả chạy thử trên máy Windows

Lần chạy ngày 10/11/2026 bằng Docker Desktop, từ 30/10 tới 04/12 trên đồng hồ mô phỏng. Chạy cao điểm và sự cố xe trong cùng phiên. Tạm dừng ở bước 70 và đợi Spark xử lý hết bản ghi đã gửi Kafka trước khi đối chiếu. Còn 42 số đo cố ý đến trễ, sẽ phát ở khung sau khi bật lại.

| Hạng mục | Kết quả quan sát |
| --- | --- |
| Quy mô danh mục | 60 khu, 3.600 hộ, 10.800 thùng, 180 xe |
| Kafka và Spark | 2 topic, 4 partition mỗi topic, 83 microbatch. Hai executor của driver hiện tại hoàn thành 1.089 và 1.085 task. Driver được khởi động lại giữa phiên và tiếp tục từ checkpoint. |
| Chất lượng | 878.885 bản ghi đầu vào, 874.767 bản ghi sạch, 4.118 bản ghi cách ly. Trong đó 2.382 bản ghi lặp, và có 2.258 bản ghi sạch đến muộn. |
| Cao điểm | Đúng 10.000 số đo có nhãn peak đã vào lớp sạch trong phút 23:59 ngày 16/11 theo đồng hồ mô phỏng. |
| Tốc độ xử lý thực | 1.201,8 bản ghi/giây tính bằng tổng input chia tổng thời gian xử lý batch. Trung vị của độ trễ tối đa mỗi batch là 17,2 giây. Giá trị lớn nhất trong phiên là 86,4 giây. |
| HDFS | Hai DataNode, 1.554 block dữ liệu được kiểm tra, hệ số nhân bản trung bình 2,0, không thiếu block hoặc thiếu bản sao. Có đủ raw, clean, quarantine và analysis. |
| Cân bằng khối lượng | Phát sinh 247.452.351 g, thu gom và đổ tại trạm 157.477.989 g, còn trong thùng 89.974.362 g. Không thùng nào lệch khối lượng. Sai lệch tổng trên xe là 0 g. |
| Hóa đơn | 7.200 hóa đơn trong hai kỳ. Không phát hiện hóa đơn sai lượng gom hoặc sai tổng, và không phát hiện giao dịch được đánh dấu khớp với sai số tiền hoặc sai hộ. |
| Đối soát | 3.807 khoản khớp, 72 khoản gửi lại. Có cả sai tiền, sai hộ, sai hóa đơn, xung đột mã giao dịch và chuyển thêm vào hóa đơn đã trả. |
| Mốc quá hạn | H-0020 quá hạn từ 01/12, H-0002 vẫn chờ đối soát. H-0001 quá hạn rồi chuyển sang đã trả lúc 03:00 ngày 03/12. Không ghi nhận lượt gom của H-0001 và H-0020 trong thời gian bị ngưng. |
| Sự cố vận hành | X-01-C hỏng và có 4 điểm đưa về hàng chờ. Có log mất tín hiệu của H-0001-O. |
| Điều chỉnh tháng 11 | 4.173 điều chỉnh được áp dụng, 92 đề xuất giảm bị chặn vì còn tồn, 6.535 thùng giữ nguyên. |
| Dashboard | Chrome headless mở thành công cả năm trang khi luồng đang chạy. Đồng hồ tiến và bộ lọc khu giữ nguyên khi chuyển trang. Trang in hóa đơn trả HTTP 200. |
| RAM tại thời điểm kiểm tra cuối | Xấp xỉ 5 GiB cộng các container. Đây là ảnh chụp tại một thời điểm. |

Số liệu hiệu năng chỉ mô tả lần chạy này, gồm cả các lần khởi động trong quá trình kiểm tra. Khi báo cáo, phân biệt tốc độ xử lý theo thời gian thực với 10.000 số đo/phút theo giờ mô phỏng. Có thể tái kiểm tra bằng [SQL kiểm kê](audit.sql) và lệnh trong [hướng dẫn nghiệm thu](BAO_CAO.md).

