from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E
import hashlib

here = Path(__file__).resolve().parent
prefix = (here / 'build_outline.py').read_text(encoding='utf-8').split('# Page 1')[0]
exec(compile(prefix, str(here / 'build_outline.py'), 'exec'))
OUT = ROOT / 'outputs' / 'De_cuong_Big_Data_Nhom_12_ban_nop.docx'

title = p('ĐỀ CƯƠNG BÀI TẬP LỚN MÔN DỮ LIỆU LỚN', True, 12, align='center', style='Title', after=140)
borders = E.SubElement(title.find(w('pPr')), w('pBdr'))
E.SubElement(borders, w('bottom'), {w('val'): 'nil'})
h('1  Tên đề tài')
p('Ứng dụng công nghệ dữ liệu lớn trong quản lý và điều phối thu gom rác thải đô thị', bold=True, align='left')
h('2  Giảng viên hướng dẫn và nhóm thực hiện')
p('Giảng viên: PGS. TS. Lê Hải Châu; PGS. TS. Nguyễn Chiến Trinh.', align='left', after=45)
p('Nhóm thực hiện: Nhóm 12', align='left', after=65)
table(['Họ và tên', 'Mã sinh viên', 'Lớp'], [
    ['Đỗ Minh Hoàng', 'B23DCKD024', 'D23CDKD02-B'],
    ['Nguyễn Hải Đăng', 'B23DCKD010', 'D23CDKD02-B'],
    ['Chu Quốc Đạt', 'B23DCKD12', 'D23CDKD02-B'],
], [3550, 2200, 3490])
h('3  Lý do chọn đề tài')
p('Lượng rác sinh hoạt tại mỗi khu vực thay đổi theo số hộ dân, thói quen sinh hoạt và thời điểm trong ngày. Nếu chỉ thu gom theo lịch cố định, một số thùng có thể bị đầy trong khi xe lại đến những nơi còn ít rác. Việc tổ chức thu gom vì vậy cần dựa vào tình trạng thực tế của từng điểm, đồng thời tính đến loại rác, sức chứa của xe và quãng đường di chuyển.')
p('Dữ liệu từ hộ gia đình, thùng rác và xe thu gom được ghi nhận liên tục theo thời gian. Việc kết hợp các nguồn dữ liệu này giúp người quản lý biết nơi nào cần thu gom trước, phân công xe phù hợp và kiểm tra công việc đã hoàn thành hay chưa. Đây cũng là cơ sở để điều chỉnh lịch thu gom và đánh giá nhu cầu của từng khu vực.')
h('4  Mục tiêu và phạm vi nghiên cứu')
p('Đề tài xây dựng hệ thống theo dõi lượng rác, tổ chức thu gom theo nhu cầu và phân tích kết quả hoạt động. Hệ thống hỗ trợ điều phối lại khi xe gặp sự cố, tự điều chỉnh tần suất thu gom từ dữ liệu lịch sử và tính mức phí tham khảo cho từng khu vực. Mục tiêu kỹ thuật là tiếp nhận và xử lý song song các đợt cao điểm từ 10.000 bản ghi trong khoảng thời gian 10 phút, kết hợp lưu trữ phân tán và đánh giá độ trễ xử lý.')
p('Phạm vi nghiên cứu gồm rác hữu cơ, rác tái chế và rác còn lại. Dữ liệu thử nghiệm được tạo bằng Python để mô phỏng hoạt động của 3.600 hộ dân, 6 khu vực, 12 điểm thu gom, 6 xe và một trạm tiếp nhận trong 14 ngày, với tổng quy mô khoảng 794.000 bản ghi trong kịch bản thử nghiệm kết hợp. Mỗi điểm có các thùng riêng cho từng loại rác; mỗi xe phục vụ một loại rác nhất định.')

page()
h('5  Nội dung nghiệp vụ')
h('Giám sát lượng rác và xác định điểm cần thu gom', 2)
p('Theo dõi lượng rác, mức đầy và thời gian rác lưu lại trong từng thùng. Hệ thống cảnh báo khi thùng gần đầy, vượt sức chứa, có rác chưa được thu gom đúng hạn hoặc cảm biến mất tín hiệu. Từ đó, người quản lý xác định được địa điểm, loại rác và mức độ cần ưu tiên thu gom.')
h('Lập lịch và phân công xe thu gom', 2)
p('Sắp xếp các điểm cần thu gom theo mức độ khẩn cấp và khoảng cách di chuyển. Xe được phân công phải phù hợp với loại rác, còn chỗ chứa và đang trong ca làm việc. Hệ thống theo dõi lượng rác đã lấy, lượng còn lại và quá trình xe đưa rác về trạm, qua đó phân biệt điểm chưa thu gom, thu gom một phần và đã thu gom hết.')
p('Khi xe gặp sự cố tại điểm dừng, công việc chưa hoàn thành được chuyển cho xe phù hợp khác. Nếu chưa bố trí được xe thay thế, hệ thống phát cảnh báo để người quản lý theo dõi. Lượng rác đã có trên xe bị hỏng vẫn được ghi nhận cho đến khi xe hoạt động trở lại.')
h('Thống kê và phân tích hoạt động thu gom', 2)
p('Tổng hợp lượng rác phát sinh theo hộ gia đình, khu vực, loại rác và thời gian; thống kê lượng đã thu gom và lượng còn lại tại các điểm. Biểu đồ thể hiện sự thay đổi lượng rác, thời gian chờ thu gom và tần suất thu gom của từng khu vực. Bản đồ hiển thị vị trí các điểm thu gom, xe và trạm tiếp nhận để theo dõi quá trình thực hiện.')
h('Điều chỉnh tần suất thu gom và tính mức phí tham khảo', 2)
p('Dựa trên lượng rác ghi nhận trong những ngày trước, hệ thống tự cập nhật lịch thu gom hằng ngày cho từng điểm và loại rác. Các điểm gần đầy hoặc chờ lâu được xem xét thu gom sớm; thông tin về sự kiện đã được báo trước cũng được đưa vào kế hoạch.')
p('Lịch sử quá tải giúp xác định những nơi cần tăng sức chứa thùng hoặc bố trí thêm lượt thu gom. Mức phí tham khảo cho từng khu vực được tính theo lượng rác sinh hoạt bình quân mỗi hộ, mức phí cơ sở và giới hạn tăng giảm. Rác từ sự kiện công cộng được thống kê riêng.')
h('6  Quy trình xử lý dữ liệu')
p('Python ghi nhật ký dữ liệu trước khi gửi vào Kafka; các bản ghi được phân vào 6 phân vùng theo điểm thu gom hoặc xe. Spark đọc dữ liệu và phân công hai executor xử lý song song: chuẩn hóa, kiểm tra dữ liệu thiếu hoặc sai, loại bản ghi trùng và tổng hợp chỉ số. Dữ liệu gốc, dữ liệu hợp lệ và dữ liệu lỗi được lưu riêng trên HDFS với hai bản sao; kết quả phục vụ tra cứu được ghi vào PostgreSQL để hiển thị trên dashboard.')
p('Bộ điều phối Python sử dụng trạng thái thùng, xe và lịch sử lượng rác để lập lịch, phân công xe, điều chỉnh tần suất và chuyển việc khi xe hỏng. Kết quả thu gom được phát lại thành sự kiện qua Kafka để Spark cập nhật các chỉ số. Spark xử lý dữ liệu lịch sử trên HDFS để lập báo cáo tổng hợp.')

page()
h('7  Công nghệ sử dụng')
bullet('Python xây dựng nguồn dữ liệu, quy tắc lập lịch và điều phối xe.')
bullet('Apache Kafka tiếp nhận và phân vùng luồng dữ liệu để phục vụ xử lý song song.')
bullet('Apache Spark Structured Streaming và Spark SQL xử lý dữ liệu theo luồng, tổng hợp và phân tích dữ liệu lịch sử.')
bullet('Hadoop HDFS lưu trữ phân tán và duy trì bản sao dữ liệu. PostgreSQL lưu các thông tin phục vụ truy vấn và báo cáo.')
bullet('Docker Compose triển khai các thành phần hệ thống. Streamlit và Plotly xây dựng dashboard, biểu đồ và bản đồ theo dõi thu gom.')
h('8  Phương pháp thực hiện và đánh giá')
p('Nhóm xây dựng dữ liệu có quy luật, triển khai hệ thống và thử nghiệm các tình huống: hoạt động thông thường, lượng rác tăng do sự kiện, cảm biến mất tín hiệu và xe gặp sự cố. Lịch cố định và lịch điều chỉnh được so sánh trên cùng nhu cầu phát sinh, đội xe và bản đồ.')
p('Hiệu quả nghiệp vụ được đánh giá qua thời gian chờ, lượng rác thu gom đúng hạn, số lần thùng quá tải, lượng rác còn lại và quãng đường xe đi. Về kỹ thuật, nhóm đo tốc độ xử lý, độ trễ và lượng bản ghi tồn đọng ở tải cao điểm trên 10.000 bản ghi mỗi đợt; kiểm tra xử lý song song, bản ghi lỗi hoặc trùng và khả năng đọc bản sao HDFS.')
h('9  Bố cục báo cáo dự kiến')
p('Chương 1  Tổng quan về dữ liệu lớn và bài toán thu gom rác thải đô thị.\nChương 2  Phân tích yêu cầu và thiết kế hệ thống: nghiệp vụ, dữ liệu, kiến trúc và các quy tắc xử lý.\nChương 3  Triển khai hệ thống, xây dựng dashboard, thực nghiệm và đánh giá kết quả.\nKết luận  Kết quả đạt được và hướng phát triển.', align='left')
h('10  Phân công thực hiện')
bullet('Đỗ Minh Hoàng: phân tích bài toán, xây dựng nguồn dữ liệu và các quy tắc lập lịch, điều phối xe.')
bullet('Nguyễn Hải Đăng: thiết kế cấu trúc dữ liệu, triển khai Kafka và xử lý chất lượng dữ liệu.')
bullet('Chu Quốc Đạt: triển khai Spark, HDFS, Docker và kết nối dữ liệu với dashboard.')
p('Cả nhóm cùng hoàn thiện giao diện, kiểm thử hệ thống, phân tích kết quả và viết báo cáo. Sản phẩm bàn giao gồm mã nguồn, dữ liệu thực nghiệm, dashboard, báo cáo và hướng dẫn sử dụng.', align='left')
h('11  Tài liệu tham khảo')
p('Tài liệu chính thức của Apache Kafka (kafka.apache.org/41/), Apache Spark (spark.apache.org/docs/4.0.4/), Apache Hadoop (hadoop.apache.org/docs/r3.5.0/) và Docker Compose (docs.docker.com/compose/).', align='left', size=10.5)

# Use readable twelve-point body text while retaining the reference page geometry.
for size in body.iter(w('sz')):
    if size.get(w('val')) == '23':
        size.set(w('val'), '24')
for spacing in body.iter(w('spacing')):
    if spacing.get(w('line')) == '260':
        spacing.set(w('line'), '270')
body.append(section)
replacements = {'word/document.xml': E.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True)}
with ZipFile(OUT, 'w', ZIP_DEFLATED) as z:
    for name, data in original.items():
        z.writestr(name, replacements.get(name, data))
with ZipFile(OUT) as z:
    assert [name for name, data in original.items() if z.read(name) != data] == ['word/document.xml']
assert hashlib.sha256(REF.read_bytes()).hexdigest() == '1ef9f9458caff8d3513364c975036dbc0b93924e4110a6ea8c22b076608e9d39'
print(OUT)
