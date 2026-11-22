from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E
import hashlib

here = Path(__file__).resolve().parent
# Reuse the source-derived A4 geometry, fonts and editable paragraph/table builders.
prefix = (here / 'build_outline.py').read_text(encoding='utf-8').split('# Page 1')[0]
exec(compile(prefix, str(here / 'build_outline.py'), 'exec'))
OUT = ROOT / 'outputs' / 'De_cuong_Big_Data_Nhom_12_ban_nop.docx'

title = p('ĐỀ CƯƠNG TIỂU LUẬN DỮ LIỆU LỚN', True, 12, align='center', style='Title', after=120)
# Word's built-in Title style carries a blue bottom rule in this template.
ppr = title.find(w('pPr'))
border = E.SubElement(ppr, w('pBdr'))
E.SubElement(border, w('bottom'), {w('val'): 'nil'})
h('1  Tên đề tài')
p('Xây dựng hệ thống dữ liệu lớn giám sát và hỗ trợ điều phối thu gom rác thải đô thị theo khu vực và loại rác', bold=True, align='left')
h('2  Giảng viên hướng dẫn và nhóm thực hiện')
p('Giảng viên: PGS. TS. Lê Hải Châu; PGS. TS. Nguyễn Chiến Trinh.     Nhóm: 12', align='left', after=65)
table(['Họ và tên', 'Mã sinh viên', 'Lớp'], [
    ['Đỗ Minh Hoàng', 'B23DCKD024', 'D23CDKD02-B'],
    ['Nguyễn Hải Đăng', 'B23DCKD010', 'D23CDKD02-B'],
    ['Chu Quốc Đạt', 'B23DCKD12', 'D23CDKD02-B'],
], [3550, 2200, 3490])
h('3  Bối cảnh và bài toán')
p('Rác thải sinh hoạt phát sinh từ các hộ gia đình được đưa đến các điểm thu gom theo khu vực và phân thành ba loại: hữu cơ, tái chế và còn lại. Lượng rác phát sinh thay đổi theo đặc điểm dân cư, thời gian và các sự kiện; trong khi số lượng xe, tải trọng và thời gian làm việc của đội thu gom có giới hạn.')
p('Nếu gom theo lịch cố định, xe có thể đến khi thùng còn ít rác, còn nơi khác lại quá tải hoặc chờ lâu. Khi cảm biến mất tín hiệu hay xe gặp sự cố, người quản lý cũng cần biết điểm nào chưa được phục vụ để điều chỉnh. Bài toán đặt ra là: với dữ liệu rác và đội xe hiện có, cần gom điểm nào, loại rác nào, lúc nào và dùng xe nào; sau đó xác nhận kết quả và điều chỉnh lịch như thế nào?')
h('4  Mục tiêu và phạm vi')
p('Xây dựng hệ thống hỗ trợ người quản lý giám sát, lập kế hoạch và theo dõi hoạt động thu gom; phân tích lượng rác theo hộ, khu vực và loại rác để điều chỉnh lịch, đánh giá năng lực thu gom và tham khảo mức phí. Đề tài vận dụng các công nghệ dữ liệu lớn trong tiếp nhận, xử lý và lưu trữ dữ liệu.')
p('Trong phạm vi thực nghiệm, dữ liệu hộ, cảm biến và xe được sinh theo quy luật cho một địa bàn gồm 360 hộ, 6 khu vực, 12 điểm gom, 6 xe và một trạm tiếp nhận; bản đồ được xây dựng để thể hiện quá trình thu gom.')

page()
h('5  Các nghiệp vụ chính')
h('5 1  Giám sát thùng và xác định nhu cầu gom', 2)
p('Theo dõi gần thời gian thực lượng tồn, sức chứa, độ đầy và thời gian chờ của từng ngăn tại mỗi điểm. Cảnh báo gần đầy, quá tải, quá hạn hoặc mất tín hiệu; từ đó xác định địa điểm và loại rác cần thu gom.')
h('5 2  Phân công, điều phối lại và xác nhận thu gom', 2)
p('Ưu tiên điểm cần gom theo mức khẩn cấp và khoảng cách; chọn xe cùng loại rác, còn tải, còn trong ca và chưa hỏng. Xe di chuyển trên bản đồ, có thể gom một phần và về trạm khi đầy. Chỉ xác nhận đã gom khi hoàn tất bốc; phần còn lại vẫn được theo dõi.')
p('Khi xe gặp sự cố tại điểm dừng, hệ thống đưa công việc chưa hoàn thành vào hàng chờ, phân công lại cho xe phù hợp hoặc cảnh báo nếu chưa có xe tiếp nhận. Lượng rác đã bốc lên xe được theo dõi đến khi xe hoạt động trở lại.')
h('5 3  Tổng hợp và trực quan hóa dữ liệu', 2)
p('Tổng hợp lượng rác phát sinh theo hộ, khu và loại; lượng giao, đã gom và còn tồn theo điểm/khu; thời gian chờ, số lần quá tải và hoạt động xe. Bản đồ thể hiện vị trí điểm gom, các loại rác, xe và trạm. Không cộng các lần đo tồn thành tổng lượng rác phát sinh.')
h('5 4  Điều chỉnh lịch, năng lực và tham khảo mức phí', 2)
p('Trên cơ sở dữ liệu lịch sử, hệ thống tự tính khoảng gom cho từng điểm và loại rác theo ngày; điểm gần đầy hoặc quá hạn có thể được phục vụ sớm. Kế hoạch được điều chỉnh theo nhu cầu sự kiện được báo trước và khả năng phục vụ của đội xe.')
p('Phân tích nhu cầu nâng sức chứa tại các điểm thường xuyên quá tải. Mức phí tham khảo theo khu được tính từ lượng rác sinh hoạt bình quân mỗi hộ, giá cơ sở và giới hạn điều chỉnh; rác từ sự kiện công cộng được tách riêng.')
h('6  Dữ liệu và luồng xử lý')
p('Dữ liệu từ hộ, điểm gom và xe được tạo bằng Python; các quy tắc nghiệp vụ xác định lịch và điều phối xe. Sự kiện được đưa vào Kafka, sau đó Spark kiểm tra, chuẩn hóa, xử lý bản tin trùng hoặc sai và tổng hợp. HDFS lưu trữ dữ liệu; PostgreSQL phục vụ truy vấn, còn dashboard hiển thị bản đồ, chỉ số, lịch và cảnh báo.')

page()
h('7  Công nghệ và phạm vi triển khai')
bullet('Python: xây dựng nguồn dữ liệu và thực hiện các quy tắc lập lịch, điều phối xe và xử lý sự cố.')
bullet('Apache Kafka: tiếp nhận và phân vùng luồng sự kiện từ các nguồn dữ liệu.')
bullet('Apache Spark Structured Streaming và Spark SQL: xử lý song song, chuẩn hóa, kiểm tra và tổng hợp dữ liệu theo luồng và theo lô.')
bullet('Hadoop HDFS: lưu trữ dữ liệu lịch sử và bản sao; PostgreSQL quản lý dữ liệu phục vụ tra cứu và trực quan hóa.')
bullet('Docker Compose: triển khai các thành phần hệ thống; Streamlit và Plotly: xây dựng dashboard và bản đồ theo dõi.')
h('8  Phương pháp đánh giá và sản phẩm')
p('Đánh giá lịch cố định và lịch điều chỉnh trên cùng bộ dữ liệu thông qua thời gian chờ, lượng thu gom đúng hạn, thời gian quá tải, lượng tồn và quãng đường. Kiểm thử tình huống xe hỏng, cảm biến mất tín hiệu, dữ liệu lỗi hoặc trùng; đối soát khối lượng và kiểm tra khả năng đọc bản sao trên HDFS.')
p('Sản phẩm: mã nguồn và cấu hình; bộ dữ liệu thực nghiệm; dashboard và bản đồ; báo cáo tiểu luận, hướng dẫn sử dụng và kết quả kiểm thử.')
h('9  Dự kiến nội dung báo cáo')
p('Chương 1  Tổng quan dữ liệu lớn và bài toán quản lý thu gom rác thải.\nChương 2  Phân tích yêu cầu, quy trình nghiệp vụ, mô hình dữ liệu và kiến trúc hệ thống.\nChương 3  Triển khai xử lý dữ liệu, thực nghiệm nghiệp vụ và đánh giá kết quả.\nKết luận  Kết quả đạt được, hạn chế và hướng phát triển.', align='left')
h('10  Phân công dự kiến')
p('Đỗ Minh Hoàng: đặc tả nghiệp vụ, xây dựng dữ liệu và quy tắc điều phối. Nguyễn Hải Đăng: Kafka, thiết kế dữ liệu, kiểm tra chất lượng và xử lý sự kiện. Chu Quốc Đạt: Spark, HDFS, Docker và tích hợp dashboard. Cả nhóm cùng kiểm thử, phân tích kết quả và hoàn thiện báo cáo.', align='left')
h('11  Tài liệu tham khảo')
p('Apache Kafka Documentation: kafka.apache.org/41/; Apache Spark Documentation: spark.apache.org/docs/4.0.4/; Apache Hadoop Documentation: hadoop.apache.org/docs/r3.5.0/; Docker Compose Documentation: docs.docker.com/compose/.', align='left', size=10.5)

body.append(section)
replacements = {'word/document.xml': E.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True)}
with ZipFile(OUT, 'w', ZIP_DEFLATED) as z:
    for name, data in original.items():
        z.writestr(name, replacements.get(name, data))
with ZipFile(OUT) as z:
    assert [name for name, data in original.items() if z.read(name) != data] == ['word/document.xml']
assert hashlib.sha256(REF.read_bytes()).hexdigest() == '1ef9f9458caff8d3513364c975036dbc0b93924e4110a6ea8c22b076608e9d39'
print(OUT)
