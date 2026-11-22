from pathlib import Path
p=Path(__file__).parent/'de_cuong_2026_11_02/rewrite_submission.py'
s=p.read_text(encoding='utf-8')
s=s.replace('Công nghệ dữ liệu lớn được sử dụng để tiếp nhận luồng dữ liệu, xử lý song song và lưu trữ phân tán.', 'Mục tiêu kỹ thuật là tiếp nhận và xử lý song song các đợt cao điểm từ 10.000 bản ghi trong khoảng thời gian 10 phút, kết hợp lưu trữ phân tán và đánh giá độ trễ xử lý.')
s=s.replace('360 hộ dân, 6 khu vực, 12 điểm thu gom, 6 xe và một trạm tiếp nhận.', '3.600 hộ dân, 6 khu vực, 12 điểm thu gom, 6 xe và một trạm tiếp nhận trong 14 ngày.')
old="p('Dữ liệu về lượng rác và hoạt động xe được gửi vào Kafka. Spark tiếp nhận dữ liệu, chuẩn hóa định dạng và đơn vị đo, kiểm tra dữ liệu thiếu hoặc sai, xử lý bản ghi trùng và tổng hợp các chỉ số. Kết quả được lưu trên HDFS và PostgreSQL để phục vụ tra cứu, phân tích và hiển thị trên dashboard. Các quy tắc lập lịch và điều phối xe được xây dựng bằng Python.')"
new="""p('Python ghi nhật ký dữ liệu trước khi gửi vào Kafka; các bản ghi được phân vào 6 phân vùng theo điểm thu gom hoặc xe. Spark đọc dữ liệu và phân công hai executor xử lý song song: chuẩn hóa, kiểm tra dữ liệu thiếu hoặc sai, loại bản ghi trùng và tổng hợp chỉ số. Dữ liệu gốc, dữ liệu hợp lệ và dữ liệu lỗi được lưu riêng trên HDFS với hai bản sao; kết quả phục vụ tra cứu được ghi vào PostgreSQL để hiển thị trên dashboard.')
p('Bộ điều phối Python sử dụng trạng thái thùng, xe và lịch sử lượng rác để lập lịch, phân công xe, điều chỉnh tần suất và chuyển việc khi xe hỏng. Kết quả thu gom được phát lại thành sự kiện qua Kafka để Spark cập nhật các chỉ số. Spark xử lý dữ liệu lịch sử trên HDFS để lập báo cáo tổng hợp.')"""
assert old in s
s=s.replace(old,new)
s=s.replace('Về kỹ thuật, nhóm kiểm tra tốc độ xử lý khi tăng lượng dữ liệu, khả năng xử lý song song, xử lý bản ghi lỗi hoặc trùng và khả năng đọc dữ liệu từ bản sao HDFS.', 'Về kỹ thuật, nhóm đo tốc độ xử lý, độ trễ và lượng bản ghi tồn đọng ở tải cao điểm trên 10.000 bản ghi mỗi đợt; kiểm tra xử lý song song, bản ghi lỗi hoặc trùng và khả năng đọc bản sao HDFS.')
p.write_text(s,encoding='utf-8')
