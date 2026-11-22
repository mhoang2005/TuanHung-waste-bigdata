"""Export precise architecture diagrams as PNG and editable SVG."""
from build_architecture import Canvas, BLUE, PURPLE, GREEN, ORANGE, INK, MUTED, OUT

def band(c, x, y, w, h, color='#ffffff', outline='#ccd5e2'):
    c.d.rounded_rectangle((x,y,x+w,y+h),radius=22,fill=color,outline=outline,width=2)
    c.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="{color}" stroke="{outline}" stroke-width="2"/>')

def box(c,x,y,w,h,title,lines,accent=BLUE,fill='#ffffff',ts=27,bs=24):
    c.box(x,y,w,h,title,lines,fill=fill,accent=accent,title_size=ts,text_size=bs,padding=22)

def placement():
    c=Canvas(2460,2490,'Kiến trúc hiện tại của dự án Smart Waste')
    c.text(60,32,'SMART WASTE | KIẾN TRÚC HIỆN TẠI',46,True)
    c.text(60,98,'Một host Windows chạy VMware và 3 VM Fedora Linux · Thiết kế dự án, chưa phải ảnh xác nhận hệ thống đã chạy',25,color=MUTED)
    c.text(60,155,'ĐỌC NHANH LUỒNG CHÍNH TỪ TRÁI SANG PHẢI',27,True)
    steps=[('1  Python','Sinh dữ liệu · host',BLUE),('2  Kafka','Nhận và lưu sự kiện',ORANGE),('3  Spark Streaming','Xử lý song song',PURPLE),('4  HDFS → Spark Batch','Lưu lịch sử → tính theo kỳ',GREEN),('5  PostgreSQL','Kết quả → Grafana',BLUE)]
    for i,(title,line,col) in enumerate(steps):
        x=60+i*480
        box(c,x,208,420,125,title,[line],accent=col,bs=24)
        if i<4: c.arrow([(x+425,270),(x+475,270)],BLUE)
    c.text(60,356,'Spark Streaming còn ghi trực tiếp trạng thái và cảnh báo vào PostgreSQL; Spark Batch đọc lại lịch sử trên HDFS.',25,color=MUTED)

    band(c,40,417,2380,1950,'#f0f4fa')
    c.text(70,438,'MÁY HOST VẬT LÝ | WINDOWS · 16 GB RAM',31,True)
    c.text(70,486,'Các dịch vụ dưới đây chạy trên host; ba khung VM ở phía dưới cũng nằm trong chính máy host này.',24,color=MUTED)
    host=[('Python Producer',['Dữ liệu IoT giả lập','Key Kafka = bin_id'],BLUE),
          ('PostgreSQL',['Danh mục / trạng thái / KPI','Cảnh báo / đề xuất'],BLUE),
          ('Health collector',['Đọc API, JMX và trạng thái','Ghi sự cố ra file / CSDL'],GREEN),
          ('Prometheus',['Thu thập metrics','Lưu số liệu sức khỏe'],GREEN),
          ('Grafana',['Dashboard nghiệp vụ','Sức khỏe và cảnh báo'],ORANGE)]
    for i,(title,lines,col) in enumerate(host):
        box(c,70+i*468,540,440,170,title,lines,accent=col,ts=27,bs=23)
    c.text(70,735,'VMware Workstation · mạng NAT VMnet8 · host 192.168.200.1 · tài nguyên dưới đây là mức dự kiến',24,color=MUTED)

    cols=[80,890,1700]
    for i,x in enumerate(cols,1):
        band(c,x,790,680,1100,'#ffffff')
        c.text(x+24,808,f'VM{i} · FEDORA LINUX',31,True)
        ram='3 GB' if i==1 else '2,5 GB'
        c.text(x+24,855,f'192.168.200.{10+i} · 2 vCPU · {ram} RAM',24,color=MUTED)
        box(c,x+25,910,630,155,f'Kafka Broker {i} + KRaft Controller {i}',[
            'Lưu leader / follower của các partition',
            f'Controller {i} là 1 trong 3 voter KRaft'
        ],ORANGE,'#fff7ed',ts=25,bs=23)
        if i==1:
            yarn=['ResourceManager: cấp tài nguyên toàn cụm','NodeManager 1: quản lý container tại VM1']
            st=['Driver streaming: client mode, ngoài YARN','Executor 1: container YARN, chạy các task']
            hd=['NameNode: quản lý tên file và vị trí block','DataNode 1: lưu block và bản sao']
        else:
            yarn=[f'NodeManager {i}: báo tài nguyên cho RM',f'Khởi chạy và theo dõi container tại VM{i}']
            st=[f'Executor {i}: chạy task trên phần dữ liệu','Task có thể thuộc nhiều bước nghiệp vụ']
            hd=[f'DataNode {i}: lưu block và bản sao','Nhận / gửi block theo giao thức HDFS']
        box(c,x+25,1105,630,150,'YARN · QUẢN LÝ TÀI NGUYÊN',yarn,PURPLE,'#f5f3ff',ts=25,bs=22)
        spark_title='SPARK · DRIVER VÀ EXECUTOR' if i==1 else 'SPARK · CONTAINER DO YARN CẤP'
        box(c,x+25,1300,630,160,spark_title,st,PURPLE,'#f5f3ff',ts=25,bs=22)
        # Data goes directly from Kafka to executor, beside the resource panel.
        c.arrow([(x+655,1010),(x+670,1010),(x+670,1360),(x+655,1360)],BLUE,width=4)
        c.arrow([(x+340,1256),(x+340,1296)],PURPLE,True)
        c.arrow([(x+340,1460),(x+340,1500)],BLUE)
        box(c,x+25,1505,630,160,'HDFS · LƯU TRỮ PHÂN TÁN',hd,GREEN,'#ecfdf5',ts=25,bs=23)
        if i==1:
            extras=['systemd: quản lý tiến trình / tự khởi động lại','Log: journalctl · UI: HDFS / YARN / Spark; Kafka qua CLI']
            title='Vận hành trên VM1'
        elif i==2:
            extras=['Không có ResourceManager hoặc NameNode riêng','NM và DN tại đây báo về các master ở VM1']
            title='Vai trò của VM2'
        else:
            extras=['Airflow: gửi job batch theo lịch, retry (giai đoạn 2)','Spark History Server: đọc event log khi cần']
            title='Điều phối batch và xem lịch sử'
        box(c,x+25,1705,630,150,title,extras,accent='#64748b',fill='#f8fafc',ts=25,bs=21)

    c.text(85,1910,'NHỮNG LIÊN KẾT GIỮA 3 VM',28,True)
    box(c,80,1960,1125,150,'Kafka: 3 partitions · RF = 2 · ví dụ phân bố',[
        'P0: leader VM1 / follower VM2    |    P1: leader VM2 / follower VM3',
        'P2: leader VM3 / follower VM1    |    Quorum KRaft: VM1 + VM2 + VM3'
    ],ORANGE,'#fff7ed',ts=26,bs=22)
    box(c,1240,1960,1130,150,'HDFS: RF = 2 · ví dụ lưu block chéo',[
        'Block A: VM1 + VM2    |    Block B: VM2 + VM3    |    Block C: VM3 + VM1',
        'Mỗi block có 2 bản tổng cộng; HDFS tự chọn DataNode nhận bản sao.'
    ],GREEN,'#ecfdf5',ts=26,bs=22)
    box(c,80,2140,2290,220,'ĐIỀU PHỐI VÀ GIÁM SÁT',[
        'Spark Driver → ResourceManager (VM1) → NodeManager → ApplicationMaster và executor containers trên các node đủ tài nguyên.',
        'Streaming Driver ở ngoài YARN trên VM1; batch Driver ở trong ApplicationMaster. Mỗi ứng dụng Spark trên YARN có AM riêng.',
        'Dịch vụ / API / JMX → Health collector → Prometheus → Grafana sức khỏe; collector ghi nhật ký sự cố.',
        'Airflow → spark-submit job batch → YARN; metadata Airflow nằm trong database riêng của PostgreSQL (giai đoạn 2).'
    ],PURPLE,'#ffffff',ts=26,bs=23)
    c.text(60,2390,'Chú ý: 3 executors là mục tiêu cấu hình, cần kiểm tra vị trí thực tế; streaming và batch dùng tài nguyên lần lượt khi thiếu RAM.',24,color=MUTED)
    c.text(60,2430,'Replication chỉ bảo vệ khi lỗi tiến trình / VM. NameNode, ResourceManager và host vật lý hiện vẫn là các điểm lỗi đơn.',24,color=MUTED)
    c.save('so-do-du-an-hien-tai-day-du')

def flow():
    c=Canvas(1900,2990,'Luồng dữ liệu Smart Waste từ nguồn tới dashboard')
    c.text(55,30,'SMART WASTE | DỮ LIỆU ĐI NHƯ THẾ NÀO',40,True)
    c.text(55,90,'Đọc theo mũi tên từ trên xuống · VM1, VM2, VM3 phối hợp xử lý cùng một ứng dụng',25,color=MUTED)
    c.arrow([(60,157),(130,157)],BLUE); c.text(145,135,'Dữ liệu',24)
    c.arrow([(390,157),(460,157)],PURPLE,True); c.text(475,135,'Điều phối / tài nguyên',24)
    c.arrow([(1010,157),(1080,157)],GREEN); c.text(1095,135,'Metrics / sự cố',24)

    box(c,390,208,1120,175,'1  PYTHON PRODUCER · HOST',[
        'Sinh sensor_reading, pickup_completed; tùy chọn waste_deposit để mô phỏng phí.',
        'Dữ liệu giả lập có thiếu, sai, trùng, trễ; phân loại sinh hoạt / công nghiệp thường.'
    ],BLUE,'#eef4ff',ts=28,bs=23)
    c.arrow([(950,383),(950,440)])
    box(c,170,447,1560,238,'2  KAFKA · XẾP SỰ KIỆN VÀ LƯU CÓ BẢN SAO',[
        'Topic waste-events: hash(bin_id) → P0 / P1 / P2. Mỗi partition có một leader và một follower.',
        'VM1 Broker 1: P0 leader + P2 follower     |     VM2 Broker 2: P1 leader + P0 follower',
        'VM3 Broker 3: P2 leader + P1 follower. Đây là ví dụ phân bố; leader có thể đổi khi có sự cố.',
        '3 KRaft controllers: quản lý metadata và bầu leader; không xử lý nghiệp vụ rác.'
    ],ORANGE,'#fff7ed',ts=28,bs=23)
    c.arrow([(950,685),(950,746)])
    c.text(980,696,'Executors trực tiếp đọc Kafka',22,color=BLUE)
    box(c,170,752,1560,356,'3  SPARK STREAMING · TÍNH TOÁN SONG SONG',[
        'VM1 Executor 1       +       VM2 Executor 2       +       VM3 Executor 3',
        'Các executors cùng chạy task do Driver phân công; mỗi executor không sở hữu riêng một nghiệp vụ.',
        'Giữ message gốc và Kafka offset; chuẩn hóa ID, thời gian, số và đơn vị; join danh mục thùng.',
        'Kiểm tra thiếu / sai / không hợp lệ; tách lỗi vào quarantine; loại trùng theo event_id và watermark.',
        'Theo dõi trạng thái thùng, đợt đầy, lần thu gom; cập nhật cảnh báo và thời gian chờ thu gom.',
        'Nhánh A → dữ liệu lịch sử trên HDFS. Nhánh B → trạng thái / cảnh báo trong PostgreSQL.'
    ],PURPLE,'#f5f3ff',ts=28,bs=23)
    c.arrow([(950,1108),(950,1228)])
    c.text(980,1123,'A  Ghi file qua HDFS client',23,color=BLUE)
    c.text(980,1160,'NameNode trả vị trí; executor ghi trực tiếp DataNode',22,color=MUTED)
    # Early serving path to right, independent of history batch.
    c.arrow([(1730,995),(1832,995),(1832,2275),(1530,2275)],BLUE,width=5)
    c.text(1750,1260,'B',28,True,color=BLUE)
    c.text(1750,1305,'Trạng',22,color=BLUE)
    c.text(1750,1338,'thái /',22,color=BLUE)
    c.text(1750,1371,'cảnh',22,color=BLUE)
    c.text(1750,1404,'báo',22,color=BLUE)
    box(c,170,1235,1560,240,'4  HDFS · 3 DATANODE LƯU BLOCK VÀ BẢN SAO',[
        'VM1 DataNode 1       +       VM2 DataNode 2       +       VM3 DataNode 3       |       RF = 2',
        '/raw: bản tin gốc      /clean: Parquet chuẩn hóa      /quarantine: dữ liệu lỗi + lý do',
        '/checkpoints: tiến độ / trạng thái Spark      /spark-events: event log      /analytics: kết quả batch',
        'NameNode trên VM1 chỉ quản lý metadata. Spark đọc một bản block phù hợp, không cộng cả bản sao.'
    ],GREEN,'#ecfdf5',ts=28,bs=23)
    c.arrow([(950,1475),(950,1536)])
    c.text(980,1485,'Đọc lịch sử + snapshot danh mục',22,color=GREEN)
    box(c,170,1544,1560,330,'5  SPARK BATCH · CÙNG CỤM YARN VÀ 3 VM',[
        'Là job khác với streaming; có Driver / executor containers riêng do YARN cấp khi chạy.',
        'Tổng hợp theo ngày, khu và loại rác; khối lượng đã gom; thời gian phản hồi; chất lượng dữ liệu.',
        'Lượng phát sinh = lượng đã gom + tồn cuối − tồn đầu; chỉ tính khi đủ dữ liệu biên.',
        'Bình quân rác sinh hoạt theo dân số; đếm đợt đầy thay vì đếm mọi bản tin báo đầy.',
        'Mô phỏng dung tích × số lần gom/ngày → mức tràn, số chuyến, chi phí → đề xuất phương án.',
        'Phí theo khu / hộ là module tùy chọn; phí từng hộ cần dữ liệu đổ rác định danh hộ.'
    ],PURPLE,'#f5f3ff',ts=28,bs=23)
    c.arrow([(950,1874),(950,1953)])
    c.text(980,1888,'Ghi kết quả tổng hợp / đề xuất',23,color=BLUE)
    box(c,170,1960,730,185,'ĐIỀU PHỐI SPARK',[
        'Driver → YARN RM (VM1) → 3 NodeManager.',
        'Mỗi NodeManager cấp container tại máy mình.',
        'Spark UI: xem executor, task, stage thực tế.'
    ],PURPLE,ts=26,bs=22)
    box(c,1000,1960,730,185,'AIRFLOW · GIAI ĐOẠN 2 · VM3',[
        'Lên lịch, phụ thuộc và retry job batch.',
        'Gửi spark-submit; batch Driver trong YARN AM.',
        'Streaming được systemd giám sát riêng.'
    ],PURPLE,ts=26,bs=22)
    # Keep the main data arrow outside the two control panels.
    c.arrow([(950,1953),(950,2188)])
    box(c,370,2195,1160,180,'6  POSTGRESQL · HOST',[
        'Danh mục: thùng / khu / dân số / đội gom / dung tích / lịch gom / tham số chi phí.',
        'Kết quả phục vụ: trạng thái mới nhất, cảnh báo, KPI và đề xuất; ghi bằng khóa ổn định.',
        'Job Spark đọc snapshot danh mục; Airflow dùng database metadata riêng khi bổ sung.'
    ],BLUE,'#eef4ff',ts=28,bs=22)
    c.arrow([(950,2375),(950,2435)])
    box(c,370,2442,1160,155,'7  GRAFANA · DASHBOARD NGHIỆP VỤ',[
        'Đọc PostgreSQL: thùng đầy / mất tín hiệu / đã gom, lượng rác theo khu và loại.',
        'Theo dõi hiệu quả thu gom và phương án dung tích / lịch gom được đề xuất.'
    ],ORANGE,'#fff7ed',ts=28,bs=23)

    c.text(60,2630,'LUỒNG GIÁM SÁT CHẠY SONG SONG VỚI LUỒNG DỮ LIỆU',27,True)
    labels=[('API / JMX / trạng thái',['Kafka · HDFS · YARN','Spark · PostgreSQL'],GREEN),
            ('Health collector',['Kiểm tra / xuất metrics','Ghi báo cáo sự cố'],GREEN),
            ('Prometheus',['Thu và lưu metrics','Đánh giá rule'],GREEN),
            ('Grafana sức khỏe',['Dashboard hạ tầng','Hiển thị cảnh báo'],ORANGE)]
    for i,(t,ls,col) in enumerate(labels):
        x=60+i*465
        box(c,x,2690,405,155,t,ls,col,ts=25,bs=22)
        if i<3:c.arrow([(x+409,2768),(x+460,2768)],GREEN)
    c.text(60,2880,'Xem lại chạy job: HDFS /spark-events → Spark History Server (VM3). Log dịch vụ: journalctl; lịch job: Airflow UI.',23,color=MUTED)
    c.text(60,2920,'Không có tầng trung gian bắt buộc giữa executor và HDFS. Replication Kafka và HDFS là hai cơ chế riêng.',23,color=MUTED)
    c.save('luong-du-lieu-hien-tai-de-doc')

if __name__=='__main__':
    placement()
    flow()
    print(OUT)
