from pathlib import Path
from html import escape
from math import atan2, cos, sin, pi
from PIL import Image, ImageDraw, ImageFont

OUT = Path(r'C:\Users\OS\Documents\Codex\2026-09-27\t-ang-h-c-m-n-2\outputs')
OUT.mkdir(parents=True, exist_ok=True)
FONT = r'C:\Windows\Fonts\segoeui.ttf'
BOLD = r'C:\Windows\Fonts\segoeuib.ttf'
INK, MUTED, BG = '#17243b', '#536279', '#f7f9fc'
BLUE, PURPLE, GREEN, ORANGE = '#2563eb', '#7c3aed', '#059669', '#d97706'


class Canvas:
    def __init__(self, w, h, title):
        self.w, self.h = w, h
        self.im = Image.new('RGB', (w, h), BG)
        self.d = ImageDraw.Draw(self.im)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><title>{escape(title)}</title><rect width="100%" height="100%" fill="{BG}"/>']
        self.overflows = []

    def text(self, x, y, text, size=26, bold=False, color=INK, anchor='left'):
        font = ImageFont.truetype(BOLD if bold else FONT, size)
        width = self.d.textlength(text, font=font)
        dx = x - width/2 if anchor == 'center' else x
        self.d.text((dx, y), text, fill=color, font=font)
        svg_anchor = 'middle' if anchor == 'center' else 'start'
        self.svg.append(f'<text x="{x}" y="{y+size}" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" font-weight="{600 if bold else 400}" fill="{color}" text-anchor="{svg_anchor}">{escape(text)}</text>')
        return width

    def wrap(self, text, font, width):
        lines, current = [], ''
        for word in text.split():
            candidate = (current + ' ' + word).strip()
            if current and self.d.textlength(candidate, font=font) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines

    def box(self, x, y, w, h, title, lines, fill='#ffffff', accent=BLUE,
            title_size=30, text_size=25, padding=25, optional=False):
        self.d.rounded_rectangle((x, y, x+w, y+h), radius=18, fill=fill, outline='#c7d2e2', width=2)
        self.d.rounded_rectangle((x, y, x+7, y+h), radius=3, fill=accent)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{fill}" stroke="#c7d2e2" stroke-width="2"/><rect x="{x}" y="{y}" width="7" height="{h}" rx="3" fill="{accent}"/>')
        yy = y+18
        font = ImageFont.truetype(BOLD, title_size)
        for line in self.wrap(title, font, w-2*padding):
            self.text(x+padding, yy, line, title_size, True)
            yy += title_size+8
        yy += 7
        font = ImageFont.truetype(FONT, text_size)
        for line in lines:
            for sub in self.wrap(line, font, w-2*padding):
                self.text(x+padding, yy, sub, text_size, color=MUTED)
                yy += text_size+9
            yy += 4
        if yy > y+h-12:
            self.overflows.append((title, yy-(y+h-12)))

    def arrow(self, points, color=BLUE, dashed=False, width=4):
        if dashed:
            for a,b in zip(points, points[1:]):
                x1,y1 = a; x2,y2=b
                length=((x2-x1)**2+(y2-y1)**2)**0.5
                if not length: continue
                for start in range(0, int(length), 21):
                    stop=min(start+12,length)
                    p1=(x1+(x2-x1)*start/length,y1+(y2-y1)*start/length)
                    p2=(x1+(x2-x1)*stop/length,y1+(y2-y1)*stop/length)
                    self.d.line((p1,p2),fill=color,width=width)
        else:
            self.d.line(points, fill=color, width=width, joint='curve')
        a,b=points[-2],points[-1]
        angle=atan2(b[1]-a[1],b[0]-a[0]); length=17
        head=[b,(b[0]-length*cos(angle-.45),b[1]-length*sin(angle-.45)),(b[0]-length*cos(angle+.45),b[1]-length*sin(angle+.45))]
        self.d.polygon(head,fill=color)
        pts=' '.join(f'{x},{y}' for x,y in points)
        dash=' stroke-dasharray="12 9"' if dashed else ''
        self.svg.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{dash}/><polygon points="'+ ' '.join(f'{x},{y}' for x,y in head)+f'" fill="{color}"/>')

    def save(self, name):
        if self.overflows:
            raise ValueError(f'Overflow: {self.overflows}')
        self.im.save(OUT / f'{name}.png')
        (OUT / f'{name}.svg').write_text('\n'.join(self.svg)+ '\n</svg>', encoding='utf-8')


def flow():
    c=Canvas(1800,2370,'Luồng dữ liệu hệ thống rác thải đô thị — mô hình chốt v1')
    c.text(60,35,'LUỒNG DỮ LIỆU · MÔ HÌNH CHỐT V1',43,True)
    c.text(60,98,'Sinh hoạt + công nghiệp thông thường · Dữ liệu giả lập · Quy tắc và mô phỏng, chưa dùng ML',26,color=MUTED)
    c.arrow([(70,154),(140,154)],BLUE); c.text(155,134,'Dữ liệu',23)
    c.arrow([(365,154),(435,154)],PURPLE,True); c.text(450,134,'Điều phối',23)
    c.arrow([(715,154),(785,154)],ORANGE); c.text(800,134,'Metrics / cảnh báo hệ thống',23)

    c.box(450,200,900,150,'1. PYTHON PRODUCER · HOST',[
        'sensor_reading: lượng tồn; pickup_completed: lượng đã gom',
        'waste_deposit định danh hộ/cơ sở: module phí từng hộ'
    ],fill='#eef4ff',text_size=24)
    c.arrow([(900,350),(900,380)])
    c.box(400,385,1000,190,'2. KAFKA · 2 BROKER TRÊN VM1 / VM2',[
        'Topic waste-events: 3 partitions; key = bin_id; RF = 2',
        'Leader được chia giữa hai broker; mỗi partition có replica ở broker kia',
        'Ba KRaft controller voters trên VM1 / VM2 / VM3'
    ],fill='#fff7ed',accent=ORANGE,text_size=24)
    c.arrow([(900,575),(900,610)])
    c.box(360,620,1080,255,'3. SPARK STREAMING · TASKS CHẠY TRÊN EXECUTORS',[
        'Executors tự đọc Kafka; giữ message gốc cùng topic/partition/offset',
        'Chuẩn hóa, kiểm tra thiếu/sai/trùng/trễ; gắn cờ dữ liệu bất thường',
        'Join danh mục; tính cửa sổ và tốc độ đầy; quản lý từng đợt cảnh báo',
        'Nhận thu gom → đóng cảnh báo, tính thời gian chờ; cập nhật trạng thái'
    ],fill='#f5f3ff',accent=PURPLE,text_size=24)
    c.box(40,635,280,215,'Driver streaming',[
        'VM1 · client mode',
        'systemd giám sát',
        'Chia và theo dõi task'
    ],accent=PURPLE,title_size=27,text_size=23)
    c.arrow([(320,730),(360,730)],PURPLE,True)
    c.box(1480,625,280,220,'Danh mục',[
        'PostgreSQL: snapshot',
        'Thùng / khu / dân số',
        'Lịch gom / chi phí',
        'Cả hai job đọc'
    ],title_size=27,text_size=22)
    c.arrow([(1480,745),(1440,745)])
    c.arrow([(900,875),(900,930)])
    c.box(360,940,1080,205,'4. HDFS · NAMENODE VM1 / DATANODE VM1, VM2, VM3',[
        '/raw: message gốc; /clean: Parquet chuẩn hóa; /quarantine: dữ liệu lỗi',
        '/checkpoints: tiến độ + state; /spark-events: event log Spark',
        'RF = 2: mỗi block có hai bản trên hai trong ba DataNode'
    ],fill='#ecfdf5',accent=GREEN,text_size=24)
    c.arrow([(900,1145),(900,1250)])
    c.text(930,1172,'Đọc lịch sử + snapshot tham chiếu',24,color=GREEN)
    c.box(360,1260,1080,275,'5. SPARK BATCH · EXECUTORS TRÊN CÙNG CỤM YARN',[
        'Hằng ngày: lượng đã gom + tồn cuối − tồn đầu; KPI thu gom và chất lượng',
        'Theo khu / loại rác; bình quân đầu người chỉ cho rác sinh hoạt',
        'Hằng tuần: mô phỏng dung tích × lịch gom → rủi ro đầy / chi phí',
        'Chọn phương án phù hợp giới hạn điểm đặt; phí khu vực là module mở rộng',
        'Dùng kg cho khối lượng; dùng lít cho mô phỏng dung tích'
    ],fill='#f5f3ff',accent=PURPLE,text_size=24)
    c.box(40,1290,280,200,'Airflow (bước 2)',[
        'VM3 · 1 task mỗi lần',
        'Gửi Spark batch',
        'Lịch / retry / phụ thuộc'
    ],accent=PURPLE,title_size=26,text_size=22)
    c.arrow([(320,1385),(360,1385)],PURPLE,True)
    c.box(1480,1310,280,180,'Driver batch / AM',[
        'YARN cluster mode',
        'YARN chọn node đủ tài nguyên'
    ],accent=PURPLE,title_size=26,text_size=22)
    c.arrow([(1480,1400),(1440,1400)],PURPLE,True)

    c.arrow([(900,1535),(900,1650)])
    c.box(400,1660,1000,190,'6. POSTGRESQL · LỚP PHỤC VỤ DASHBOARD',[
        'Trạng thái, cảnh báo, KPI, đề xuất; kết quả ghi bằng khóa ổn định / upsert',
        'Database nghiệp vụ và database metadata Airflow tách riêng',
        'Kết quả phí theo kỳ được kiểm tra để chạy lại không tạo phí trùng'
    ],fill='#eef4ff',text_size=24)
    c.arrow([(1440,855),(1460,855),(1460,900),(1780,900),(1780,1745),(1400,1745)])
    c.text(1480,986,'KPI / cảnh báo',24,color=BLUE)
    c.text(1480,1022,'tức thời',24,color=BLUE)
    c.arrow([(900,1850),(900,1885)])
    c.box(400,1895,1000,155,'7. GRAFANA · DASHBOARD NGHIỆP VỤ',[
        'Tình trạng thùng, lượng rác, chất lượng dữ liệu và hiệu quả thu gom',
        'So sánh phương án dung tích / lịch gom; phí ước tính khi triển khai module'
    ],fill='#fff7ed',accent=ORANGE,text_size=24)

    c.text(60,2080,'GIÁM SÁT LÀ LUỒNG RIÊNG',28,True)
    c.box(60,2130,475,150,'Exporters / metrics endpoint',[
        'Linux Node Exporter / Windows exporter',
        'Kafka, Hadoop, Spark progress metrics'
    ],accent=ORANGE,title_size=26,text_size=22)
    c.box(665,2130,405,150,'Prometheus · host',[
        'Scrape và lưu chuỗi thời gian',
        'Trạng thái / tốc độ / độ trễ'
    ],accent=ORANGE,title_size=26,text_size=22)
    c.box(1200,2130,540,150,'Grafana · dashboard hệ thống',[
        'Xem metrics, đặt quy tắc cảnh báo lỗi',
        'Đối chiếu log Airflow / Spark / systemd'
    ],accent=ORANGE,title_size=26,text_size=22)
    c.arrow([(535,2205),(665,2205)],ORANGE)
    c.arrow([(1070,2205),(1200,2205)],ORANGE)
    c.text(60,2310,'Phí từng hộ cần sự kiện bỏ rác định danh. ML và Loki chưa thuộc v1. Airflow tích hợp sau khi pipeline lõi ổn.',24,color=MUTED)
    c.save('luong-du-lieu-chot-v1')


def placement():
    c=Canvas(1800,1930,'Bố trí host và ba máy ảo — mô hình chốt v1')
    c.text(60,35,'BỐ TRÍ HOST + 3 VM FEDORA',43,True)
    c.text(60,98,'Một máy vật lý 16 GB RAM · Các VM dùng chung CPU, RAM và ổ đĩa của host',26,color=MUTED)
    c.box(60,155,1680,260,'HOST WINDOWS · VMWARE + NGUỒN DỮ LIỆU + GIAO DIỆN',[
        'Python producer giả lập; PostgreSQL: danh mục + kết quả + database metadata Airflow riêng',
        'Prometheus, Grafana và Windows exporter; trình duyệt mở Grafana / Airflow / Spark History Server',
        'Dịch vụ host dùng bản cài phù hợp Windows; Airflow và các dịch vụ cụm chạy trong Fedora',
        'Mạng VMware host-only: IP ổn định, hostname truy cập được; Kafka advertised listeners dùng IP VM'
    ],fill='#eef4ff',text_size=26)
    c.text(60,466,'TRIỂN KHAI DỊCH VỤ',29,True)
    c.text(60,510,'Spark executor là tiến trình YARN khởi chạy khi có ứng dụng, không phải dịch vụ cài riêng thường trực.',25,color=MUTED)

    c.box(60,570,530,600,'VM1 · ĐIỀU PHỐI + WORKER',[
        'Kafka Broker 1 + KRaft controller voter 1',
        'HDFS NameNode (duy nhất) + DataNode 1',
        'YARN ResourceManager (duy nhất) + NodeManager 1',
        'Spark streaming Driver: client mode, do systemd giám sát',
        'YARN có thể khởi chạy Spark executor / ApplicationMaster',
        'Node Exporter + metrics Kafka/Hadoop/Spark'
    ],fill='#ffffff',title_size=28,text_size=25)
    c.box(635,570,530,600,'VM2 · WORKER + KAFKA',[
        'Kafka Broker 2 + KRaft controller voter 2',
        'HDFS DataNode 2',
        'YARN NodeManager 2',
        'YARN khởi chạy Spark executor / ApplicationMaster nếu đủ tài nguyên',
        'Node Exporter + metrics Kafka/Hadoop/Spark',
        'Kafka RF=2: partition có một bản ở mỗi broker'
    ],fill='#ffffff',title_size=28,text_size=25)
    c.box(1210,570,530,600,'VM3 · WORKER + BATCH',[
        'KRaft controller voter 3: không phải Kafka broker',
        'HDFS DataNode 3 + YARN NodeManager 3',
        'YARN khởi chạy Spark executor / ApplicationMaster',
        'Airflow + Spark submit client: tích hợp giai đoạn 2',
        'Spark History Server bật khi xem lịch sử job',
        'Node Exporter + metrics Hadoop/Spark'
    ],fill='#ffffff',title_size=28,text_size=25)

    c.text(60,1200,'YARN: CẤP TÀI NGUYÊN VÀ KHỞI CHẠY TIẾN TRÌNH',28,True)
    c.box(60,1255,450,150,'ResourceManager · VM1',[
        'Lập lịch trong ngân sách CPU/RAM',
        'do từng NodeManager khai báo'
    ],fill='#f5f3ff',accent=PURPLE,title_size=25,text_size=23)
    c.box(650,1255,480,150,'NodeManager · cả 3 VM',[
        'Báo tài nguyên; quản lý containers',
        'Chừa RAM cho OS / các daemon'
    ],fill='#f5f3ff',accent=PURPLE,title_size=25,text_size=23)
    c.box(1270,1255,470,150,'YARN containers',[
        'Chạy Spark executors và AM',
        'Batch Driver nằm trong AM/YARN'
    ],fill='#f5f3ff',accent=PURPLE,title_size=25,text_size=23)
    c.arrow([(510,1330),(650,1330)],PURPLE,True)
    c.arrow([(1130,1330),(1270,1330)],PURPLE,True)
    c.text(60,1445,'HDFS: METADATA VÀ NỘI DUNG FILE LÀ HAI ĐƯỜNG KHÁC NHAU',28,True)
    c.box(60,1500,1680,190,'NameNode trả vị trí block; executors trực tiếp đọc/ghi các DataNode',[
        'Ba DataNode; RF=2: ví dụ Block A ở VM1+VM2, Block B ở VM2+VM3, Block C ở VM3+VM1',
        'Spark không xử lý hai replica thành hai bản dữ liệu; mỗi block chỉ đọc một replica phù hợp',
        'HDFS /spark-events → Spark History Server; log lỗi chi tiết: Airflow UI và journalctl'
    ],fill='#ecfdf5',accent=GREEN,title_size=27,text_size=24)

    c.text(60,1710,'GIỚI HẠN VÀ CÁCH DEMO',28,True)
    c.text(60,1760,'• Không bảo đảm mặc định luôn có một executor mỗi VM; kiểm tra phân bố task bằng Spark UI.',25,color=MUTED)
    c.text(60,1800,'• Demo Kafka failover bằng dừng tiến trình Kafka; tắt VM1 còn làm mất NameNode, RM và streaming Driver.',25,color=MUTED)
    c.text(60,1840,'• Airflow là giai đoạn 2; batch chạy lần lượt. Toàn bộ stack phải được đo RAM trước khi bật đồng thời.',25,color=MUTED)
    c.text(60,1880,'• Replication bảo vệ ở cấp tiến trình/VM; NameNode, RM và host vật lý chưa có HA.',25,color=MUTED)
    c.save('bo-tri-may-chot-v1')


if __name__ == '__main__':
    flow()
    placement()
    print('Created diagrams in', OUT)
