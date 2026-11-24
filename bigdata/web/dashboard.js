const el = id => document.getElementById(id);

const names = {
  organic:'Hữu cơ (O)', recycle:'Tái chế (R)', other:'Còn lại (C)',
  running:'ĐANG CHẠY DEMO', paused:'ĐANG TẠM DỪNG', stopped:'ĐÃ DỪNG',
  overload:'Quá tải (>100%)', full:'Đã đầy (95–100%)', high:'Gần đầy (75–94%)', stale:'Để quá lâu', normal:'Bình thường (<75%)',
  paid:'Đã thanh toán đủ', unpaid:'Chưa đóng (còn hạn)', overdue:'Quá hạn · Ngừng gom', review:'Đóng thiếu (chờ đóng bù)',
  none:'Chưa phát hành HĐ', matched:'Khớp hợp lệ', duplicate:'Giao dịch gửi trùng', assigned:'Đã phân xe',
  collecting:'Xe đang gom', completed:'Đã gom xong', partial:'Gom một phần (xe đầy)', requeued:'Mở lại chờ xe',
  suspended:'Bỏ qua (nợ quá hạn)', no_pickup:'Bỏ qua (Ngừng gom)', waiting_pickup:'Đang chờ phân xe', empty:'Thùng rỗng',
  broken:'Xe gặp sự cố', recovered:'Xe đã sửa xong', idle:'Sẵn sàng chạy', standby:'Tạm rút (dự phòng)', working:'Đang làm việc',
  lost:'Mất tín hiệu cảm biến', restored:'Đã có tín hiệu lại', sensor:'Cảm biến đo thùng', pickup:'Xe thu gom rác',
  vehicle:'Điều phối xe', signal:'Tín hiệu IoT', dump:'Xe đổ rác tại trạm', arrived:'Xe tới hộ dân',
  unloaded:'Đã đổ vào trạm', returning:'Xe quay về trạm', applied:'Đã tự động áp dụng', unchanged:'Giữ nguyên mức cũ',
  blocked_capacity:'Chặn giảm (rác tồn > mức mới)', underpaid:'Thiếu tiền (quá 1 tháng sẽ ngừng gom)',
  overpaid_refund:'Thừa tiền (Đã gom · Liên hệ hoàn tiền)', amount_mismatch:'Thiếu tiền (quá 1 tháng sẽ ngừng gom)',
  house_mismatch:'Sai mã hộ (Liên hệ hỗ trợ)', invoice_not_found:'Sai mã hóa đơn (Liên hệ hỗ trợ)',
  same_transaction:'Gửi trùng mã giao dịch (bỏ qua)', transaction_conflict:'Trùng mã GD nhưng khác số tiền',
  invoice_already_paid:'Đóng dư HĐ đã trả (Liên hệ hoàn tiền)', exact_match:'Đúng mã HĐ & đủ số tiền'
};

const pages = {
  operations:[
    'BƯỚC 01 / CẢM BIẾN IOT & ĐIỀU PHỐI THU GOM',
    'Giám sát thùng rác & Phân xe trực tiếp',
    'Theo dõi tức thời độ đầy từng thùng, tỷ lệ hộ chưa gom, xe đang chạy và luồng sự kiện cảm biến IoT.',
    '<b>Cách trình bày Bước 1:</b> Bảng hiển thị 30 thùng đại diện theo dõi tại chỗ (không giật nhảy dòng). Hộ nào đầy <b>≥ 75%</b> hoặc quá lịch được tự động phân xe gần nhất. Nhóm <b>5% hộ nợ quá hạn</b> bị gắn nhãn <b>Ngừng gom</b> và xe tự bỏ qua.'
  ],
  analysis:[
    'BƯỚC 02 / THỐNG KÊ & TRỰC QUAN HÓA BIG DATA',
    'Phân tích khối lượng, Giờ cao điểm & Tài chính',
    'Tổng hợp phát sinh vs thu gom theo ngày, khung giờ cao điểm 24h, phân bố 60 khu và hiệu quả tài chính.',
    '<b>Cách trình bày Bước 2:</b> Rê chuột vào bất kỳ cột biểu đồ nào để xem số liệu chi tiết. Biểu đồ 24h nổi bật 2 đỉnh cao điểm <b>05–06h sáng</b> và <b>17–20h tối</b>; lọc thử một Khu cụ thể để xem chi tiết từng hộ.'
  ],
  planning:[
    'BƯỚC 03 / QUY HOẠCH TỰ ĐỘNG THÙNG · LỊCH · XE',
    'Tự động cân chỉnh dung tích, tần suất & đội xe',
    'Cuối mỗi kỳ tháng, hệ thống tự động điều chỉnh cấu hình cho tháng sau dựa trên sản lượng thực tế.',
    '<b>Cách trình bày Bước 3:</b> Phát sinh <b>&gt; 80%</b> sức chứa chu kỳ → tự tăng thùng <b>+5L</b> &amp; rút lịch <b>-24h</b>. Dưới <b>25%</b> → giảm <b>-5L</b> &amp; giãn <b>+24h</b> (tự chặn giảm nếu rác tồn lớn hơn mức mới). Khu vượt 9 lượt/ngày → cấp thêm <b>Xe thứ 2</b>.'
  ],
  finance:[
    'BƯỚC 04 / HÓA ĐƠN & ĐỐI SOÁT THANH TOÁN',
    'Tính phí rác, Đối soát giao dịch & Ngừng gom hộ nợ',
    'Mỗi hộ 1 hóa đơn/tháng = 15.000 đ cơ bản + đơn giá theo kg từng loại rác, tự động đối soát từ ngân hàng.',
    '<b>Cách trình bày Bước 4:</b> Bấm <b>In PDF</b> để xem chi tiết hóa đơn. Hộ không đóng hoặc đóng thiếu sau 1 tháng chuyển sang <b>Quá hạn · Ngừng gom</b> và quay lại khép vòng tròn từ chối thu gom ở Bước 1.'
  ],
  health:[
    'NỀN TẢNG KỸ THUẬT / KIẾN TRÚC BIG DATA',
    'Đường ống Kafka → Spark Streaming → HDFS & PostgreSQL',
    'Giám sát luồng dữ liệu phân tán thời gian thực, khử trùng lặp, cách ly dữ liệu bẩn và lưu trữ Parquet 4 lớp.',
    '<b>Cách trình bày Bước 5:</b> Bộ sinh sự kiện bắn thẳng vào <b>Kafka (2 topic × 4 partition)</b> → <b>Spark Streaming (2 Executor, trigger 3s)</b> xử lý, tách bản ghi lỗi vào <b>Quarantine</b>, ghi <b>HDFS Parquet 4 lớp (RF=2)</b> và commit nguyên tử vào <b>PostgreSQL</b>.'
  ]
};

const display = v => names[v] || v || '—';
const esc = v => String(v ?? '—').replaceAll('&','&amp;').replaceAll('<','&lt;')
  .replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
const number = v => v == null ? '—' : Number(v).toLocaleString('vi-VN',{maximumFractionDigits:2});
const kg = v => v == null ? '—' : number(v/1000)+' kg';
const money = v => v == null ? '—' : number(v)+' đ';
const time = v => v ? new Date(v).toLocaleString('vi-VN',{timeZone:'Asia/Ho_Chi_Minh',hour12:false}) : '—';

const cardIcons = {
  good:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M20 6L9 17l-5-5"/></svg>',
  warn:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 9v4m0 4h.01"/><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>',
  bad:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="9"/><path d="M15 9l-6 6M9 9l6 6"/></svg>',
  info:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="9"/><path d="M12 16v-4m0-4h.01"/></svg>'
};

const badge = v => '<span class="tag '+(['paid','matched','completed','applied','running','idle','exact_match','overpaid_refund'].includes(v) ? 'good'
  : ['broken','overdue','overload','no_pickup','suspended'].includes(v) ? 'bad'
  : ['review','high','full','stale','lost','partial','underpaid','standby'].includes(v) ? 'warn' : '')+'">'+esc(display(v))+'</span>';

const fillMeter = (pct, grams, maxGrams, capL, partial) => {
  if (pct == null) return partial ? '<span class="mini-tag warn">⚡ Chờ số đo sau gom 1 phần</span>' : '<span class="mini-tag">⏳ Chờ số đo</span>';
  const n = Number(pct);
  const w = Math.min(100, Math.max(0, n));
  const barTone = n > 100 ? 'bad' : n >= 95 ? 'full' : n >= 75 ? 'warn' : '';
  const tagTone = n >= 95 ? 'bad' : n >= 75 ? 'warn' : 'good';
  const word = n > 100 ? 'Quá tải' : n >= 95 ? 'Đã đầy' : n >= 75 ? 'Gần đầy' : 'Ổn định';
  const sub = grams == null ? '' :
    '<div class="fill-sub"><span>'+kg(grams)+(maxGrams?' / '+kg(maxGrams):'')+'</span>'+(capL?'<span>'+number(capL)+'L</span>':'')+'</div>';
  return '<div class="fill-stack"><div class="fill-cell"><div class="fill-track"><div class="fill-bar '+barTone+'" style="width:'+w+'%"></div></div><strong class="fill-pct-num">'+number(n)+'%</strong><span class="mini-tag '+tagTone+'">'+word+'</span></div>'+sub+'</div>';
};

const shortCat = {organic:'Hữu cơ', recycle:'Tái chế', other:'Còn lại'};
const shortPay = {paid:'Đã đóng', unpaid:'Còn hạn', review:'Đóng thiếu', overdue:'Quá hạn', none:'Chưa có HĐ'};
const catBadge = c => '<span class="cat-tag '+esc(c)+'">'+esc(shortCat[c] || display(c))+'</span>';

const stateCell = r => {
  if (r.payment === 'overdue') return '<span class="mini-tag bad">⛔ Nợ quá hạn</span>';
  const payText = '<span class="pay-line"><i class="pay-dot '+esc(r.payment)+'"></i>'+esc(shortPay[r.payment] || display(r.payment))+'</span>';
  if (r.is_late) return '<div class="state-stack"><span class="mini-tag warn">⏱ Quá lịch gom</span><span class="pay-sub">'+esc(shortPay[r.payment] || '')+'</span></div>';
  return payText;
};

const dispatchPill = (r, collectedFresh) => {
  const truck = r.assigned_truck ? '<code>'+esc(r.assigned_truck)+'</code>' : '';
  if (r.payment === 'overdue') return '<span class="dispatch-pill bad">⛔ Ngừng gom</span>';
  if (r.last_task === 'partial') return '<span class="dispatch-pill warn">⚡ Gom 1 phần '+truck+'</span>';
  if (r.last_task === 'assigned' || r.last_task === 'collecting') return '<span class="dispatch-pill warn">🚚 Đang gom '+truck+'</span>';
  if (r.broken_truck && (r.needs || r.last_task === 'requeued')) return '<span class="dispatch-pill bad">🔧 Xe <code>'+esc(r.broken_truck)+'</code> đang sửa</span>';
  if (r.last_task === 'requeued') return '<span class="dispatch-pill warn">↻ Chờ xe thay thế</span>';
  if (r.needs) return '<span class="dispatch-pill">⏳ Chờ phân xe</span>';
  if (r.last_task === 'completed' && r.broken_truck && r.assigned_truck && r.assigned_truck !== r.broken_truck) {
    return '<span class="dispatch-pill '+(collectedFresh?'collected':'good')+'">✓ Đã gom '+truck+' · <small>🔧 '+esc(r.broken_truck)+' sửa</small></span>';
  }
  if (r.broken_truck) return '<span class="dispatch-pill warn">🔧 Xe <code>'+esc(r.broken_truck)+'</code> đang sửa</span>';
  if (r.last_task === 'completed') return '<span class="dispatch-pill '+(collectedFresh?'collected':'good')+'">✓ '+(collectedFresh?'Vừa gom xong ':'Đã gom ')+truck+'</span>';
  return '<span class="dispatch-pill">— Chưa đầy</span>';
};

const explainTruck = id => {
  if (!id) return '—';
  const extra = id.endsWith('-2') ? ' <span class="mini-tag good">Xe #2</span>' : ' <span class="mini-tag">Xe #1</span>';
  return '<b>'+esc(id)+'</b>'+extra;
};

const table = (columns,rows,rowAttrs) => rows.length ? '<div class="table-wrap"><table><thead><tr>'+
  columns.map(v=>'<th scope="col">'+esc(v)+'</th>').join('')+'</tr></thead><tbody>'+
  rows.map((row,i)=>'<tr'+(rowAttrs?.[i]?' '+rowAttrs[i]:'')+'>'+row.map(v=>'<td>'+v+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>'
  : '<p class="empty">Chưa có dữ liệu phù hợp bộ lọc đang chọn.</p>';

const panel = (title,body) => '<section class="panel"><h2>'+esc(title)+'</h2>'+body+'</section>';

const cards = items => {
  const cls = items.length === 4 ? ' cols-4' : (items.length === 3 || items.length >= 5) ? ' cols-3' : '';
  return '<div class="cards'+cls+'">'+items.map(([title,value,detail,tone]) => {
    const t = tone || 'info';
    return '<div class="card '+t+'"><div class="card-top"><span class="card-label">'+esc(title)+'</span><span class="card-ico">'+
      (cardIcons[t] || cardIcons.info)+'</span></div><strong class="'+(String(value).length>15?'text':'')+'">'+esc(value)+'</strong>'+
      (detail?'<small class="sub">'+esc(detail)+'</small>':'')+'</div>';
  }).join('')+'</div>';
};

const terminal = (id,title) => '<section class="panel terminal-panel" data-terminal="'+id+'">'+
  '<div class="terminal-head"><h2>'+esc(title)+'</h2><span class="live-badge"><i class="live-dot"></i>LIVE STREAM</span></div>'+
  '<div class="terminal-stream" role="log" aria-live="off" tabindex="0" aria-label="'+esc(title)+'">'+
  '<div class="terminal-empty">Đang chờ sự kiện…</div></div></section>';

function chart(rows) {
  if (!rows.length) return '<p class="empty">Chưa có số liệu trong kỳ tháng này.</p>';
  const max = Math.max(1,...rows.flatMap(r=>[Number(r.generated)/1000,Number(r.collected)/1000]));
  const w = 900, h = 232, base = 195, left = 60, group = (w-left-14)/rows.length;
  const defs = '<defs><linearGradient id="gGen" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#128b6d"/><stop offset="100%" stop-color="#0b614c"/></linearGradient>'+
    '<linearGradient id="gCol" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#6eb4d1"/><stop offset="100%" stop-color="#488ca8"/></linearGradient></defs>';
  const bars = rows.map((row,index)=>{
    const g = Number(row.generated)/1000, c = Number(row.collected)/1000;
    const pct = g > 0 ? c*100/g : 0;
    const x = left+index*group, gw = Math.min(20, Math.max(3, group*.34));
    const tip = '<b>Ngày '+esc(row.label)+'</b>Phát sinh: '+number(g)+' kg<br>Đã thu gom: '+number(c)+' kg ('+number(pct)+'%)';
    const r1 = '<rect x="'+(x+2)+'" y="'+(base-g/max*155)+'" width="'+gw+'" height="'+(g/max*155)+'" rx="3" fill="url(#gGen)" data-tip="'+esc(tip)+'"/>';
    const r2 = '<rect x="'+(x+4+gw)+'" y="'+(base-c/max*155)+'" width="'+gw+'" height="'+(c/max*155)+'" rx="3" fill="url(#gCol)" data-tip="'+esc(tip)+'"/>';
    return r1+r2+(index%Math.ceil(rows.length/15)===0?'<text x="'+(x+gw)+'" y="216" text-anchor="middle">'+esc(row.label.slice(-2))+'</text>':'');
  }).join('');
  const grid = [0,.25,.5,.75,1].map(p=>'<path d="M '+left+' '+(base-p*155)+' H 892" stroke="#e2ece7" stroke-dasharray="'+(p?'3 4':'')+'"/>'+
    '<text x="0" y="'+(base-p*155+4)+'">'+number(Math.round(max*p))+'</text>').join('');
  return '<div class="legend"><span><i class="green"></i>Phát sinh (kg)</span><span><i class="blue"></i>Đã thu gom (kg)</span><span>Rê chuột vào cột để xem chi tiết</span></div>'+
    '<svg viewBox="0 0 '+w+' '+h+'" class="chart" role="img" aria-label="Biểu đồ phát sinh và thu gom theo ngày">'+defs+grid+bars+'</svg>';
}

function hourlyChart(rows) {
  const byHour = new Map((rows||[]).map(r=>[Number(r.hour), r]));
  const hours = Array.from({length:24}, (_,h)=>({
    hour:h, pickups:Number(byHour.get(h)?.pickups||0), kg:Number(byHour.get(h)?.grams||0)/1000
  }));
  const max = Math.max(1, ...hours.map(r=>r.pickups));
  if (!rows || !rows.length) return '<p class="empty">Chưa có sự kiện thu gom trong kỳ này.</p>';
  const w = 700, h = 228, base = 188, left = 48, bw = (w - left - 14) / 24;
  const defs = '<defs><linearGradient id="gPeak" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#f59e0b"/><stop offset="100%" stop-color="#d96b12"/></linearGradient>'+
    '<linearGradient id="gOff" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#87bfd6"/><stop offset="100%" stop-color="#5d9cb8"/></linearGradient></defs>';
  const peakBg = (fromH, spanH, label) => {
    const x = left + fromH * bw, width = spanH * bw;
    return '<rect x="'+x+'" y="22" width="'+width+'" height="'+(base-22)+'" fill="#fff6e7" rx="6"/>'+
      '<text x="'+(x+width/2)+'" y="15" text-anchor="middle" style="fill:#b45309;font-size:10.5px;font-weight:700">'+label+'</text>';
  };
  const bars = hours.map(r=>{
    const isPeak = (r.hour >= 5 && r.hour <= 6) || (r.hour >= 17 && r.hour <= 20);
    const barH = r.pickups / max * 145;
    const x = left + r.hour * bw + 3, width = Math.max(8, bw - 6);
    const lbl = String(r.hour).padStart(2,'0')+'h';
    const tip = '<b>Khung '+lbl+':00 – '+lbl+':59</b>'+(isPeak?'🔥 Giờ cao điểm':'Giờ thường')+'<br>Lượt thu gom: '+number(r.pickups)+' lượt<br>Khối lượng: '+number(r.kg)+' kg';
    return '<rect x="'+x+'" y="'+(base-barH)+'" width="'+width+'" height="'+barH+'" rx="3" fill="url(#'+(isPeak?'gPeak':'gOff')+')" data-tip="'+esc(tip)+'"/>'+
      ((r.hour%3===0 || r.hour===5 || r.hour===17 || r.hour===20) ? '<text x="'+(x+width/2)+'" y="208" text-anchor="middle">'+lbl+'</text>' : '');
  }).join('');
  const grid = [0,.25,.5,.75,1].map(p=>'<path d="M '+left+' '+(base-p*145)+' H '+(w-10)+'" stroke="#e2ece7" stroke-dasharray="'+(p?'3 4':'')+'"/>'+
    '<text x="0" y="'+(base-p*145+4)+'">'+number(Math.round(max*p))+'</text>').join('');
  const peakSum = hours.filter(r=>(r.hour>=5&&r.hour<=6)||(r.hour>=17&&r.hour<=20)).reduce((s,r)=>s+r.pickups,0);
  const allSum = hours.reduce((s,r)=>s+r.pickups,0);
  return '<div class="legend"><span><i class="amber"></i>Cao điểm (05–06h &amp; 17–20h): <b>'+number(peakSum)+' lượt ('+number(allSum?peakSum*100/allSum:0)+'%)</b></span>'+
    '<span><i class="blue"></i>Các giờ khác (rải đều)</span></div>'+
    '<svg viewBox="0 0 '+w+' '+h+'" class="chart" role="img" aria-label="Biểu đồ giờ cao điểm thu gom 24h">'+defs+
    peakBg(5,2,'Cao điểm sáng')+peakBg(17,4,'Cao điểm tối')+grid+bars+'</svg>';
}

function zoneChart(rows) {
  if (!rows || !rows.length) return '<p class="empty">Chưa có dữ liệu theo khu.</p>';
  const max = Math.max(1, ...rows.flatMap(r=>[Number(r.generated)/1000, Number(r.collected)/1000]));
  const w = 900, h = 230, base = 192, left = 56, group = (w - left - 12) / rows.length;
  const step = Math.max(1, Math.ceil(rows.length / 12));
  const bars = rows.map((r,i)=>{
    const g = Number(r.generated)/1000, c = Number(r.collected)/1000;
    const pct = g > 0 ? c*100/g : 0;
    const x = left + i * group, gw = Math.min(24, Math.max(2.5, group * .36));
    const tip = '<b>Khu '+String(r.zone).padStart(2,'0')+'</b>Phát sinh: '+number(g)+' kg<br>Đã gom: '+number(c)+' kg ('+number(pct)+'%)<br>Lượt xe: '+number(r.pickups);
    const r1 = '<rect x="'+(x+1)+'" y="'+(base-g/max*152)+'" width="'+gw+'" height="'+(g/max*152)+'" rx="2" fill="#108568" data-tip="'+esc(tip)+'"/>';
    const r2 = '<rect x="'+(x+2+gw)+'" y="'+(base-c/max*152)+'" width="'+gw+'" height="'+(c/max*152)+'" rx="2" fill="#5da1be" data-tip="'+esc(tip)+'"/>';
    const lbl = (i % step === 0 || i === rows.length - 1) ? '<text x="'+(x+gw)+'" y="213" text-anchor="middle">K'+String(r.zone).padStart(2,'0')+'</text>' : '';
    return r1 + r2 + lbl;
  }).join('');
  const grid = [0,.25,.5,.75,1].map(p=>'<path d="M '+left+' '+(base-p*152)+' H 892" stroke="#e2ece7" stroke-dasharray="'+(p?'3 4':'')+'"/>'+
    '<text x="0" y="'+(base-p*152+4)+'">'+number(Math.round(max*p))+'</text>').join('');
  return '<div class="legend"><span><i class="green"></i>Phát sinh (kg)</span><span><i class="blue"></i>Đã thu gom (kg)</span><span>60 khu · Rê chuột để xem từng khu</span></div>'+
    '<svg viewBox="0 0 '+w+' '+h+'" class="chart" role="img" aria-label="Biểu đồ khối lượng rác theo từng khu">'+grid+bars+'</svg>';
}

function financeMonthlyChart(rows) {
  if (!rows || !rows.length) return '<p class="empty">Chưa có dữ liệu hóa đơn tài chính.</p>';
  const max = Math.max(1, ...rows.map(r=>Number(r.billed_vnd)/1e6));
  const w = 680, h = 205, base = 170, left = 54, group = (w - left - 18) / rows.length;
  const bars = rows.map((r,i)=>{
    const paid = Number(r.collected_vnd)/1e6, pend = Number(r.pending_vnd)/1e6, over = Number(r.overdue_vnd)/1e6;
    const total = Number(r.billed_vnd)/1e6;
    const bw = Math.min(52, Math.max(20, group * .46));
    const x = left + i * group + (group - bw)/2;
    const hPaid = paid / max * 134, hPend = pend / max * 134, hOver = over / max * 134;
    const yPaid = base - hPaid, yPend = yPaid - hPend, yOver = yPend - hOver;
    const tip = '<b>Kỳ '+esc(r.month.slice(0,7))+' ('+number(r.total_cnt)+' HĐ)</b>Tổng xuất: '+money(r.billed_vnd)+'<br>Đã thu: '+money(r.collected_vnd)+'<br>Chờ thu: '+money(r.pending_vnd)+'<br>Quá hạn: '+money(r.overdue_vnd);
    return '<rect x="'+x+'" y="'+yPaid+'" width="'+bw+'" height="'+hPaid+'" rx="2" fill="#108568" data-tip="'+esc(tip)+'"/>'+
      '<rect x="'+x+'" y="'+yPend+'" width="'+bw+'" height="'+hPend+'" fill="#7aa0aa" data-tip="'+esc(tip)+'"/>'+
      '<rect x="'+x+'" y="'+yOver+'" width="'+bw+'" height="'+hOver+'" rx="2" fill="#c93b2b" data-tip="'+esc(tip)+'"/>'+
      '<text x="'+(x+bw/2)+'" y="'+(Math.max(14, yOver - 5))+'" text-anchor="middle" style="font-weight:700;fill:#0f2c27">'+number(total)+' tr</text>'+
      '<text x="'+(x+bw/2)+'" y="190" text-anchor="middle">'+esc(r.month.slice(0,7))+'</text>';
  }).join('');
  const grid = [0,.25,.5,.75,1].map(p=>'<path d="M '+left+' '+(base-p*134)+' H '+(w-10)+'" stroke="#e2ece7" stroke-dasharray="'+(p?'3 4':'')+'"/>'+
    '<text x="0" y="'+(base-p*134+4)+'">'+number(Math.round(max*p))+' tr</text>').join('');
  const rowsHtml = rows.map(r=>{
    const rate = Number(r.billed_vnd) ? Number(r.collected_vnd)*100/Number(r.billed_vnd) : 0;
    const overRate = Number(r.billed_vnd) ? Number(r.overdue_vnd)*100/Number(r.billed_vnd) : 0;
    return '<div class="eff-meta"><b>Kỳ '+esc(r.month.slice(0,7))+' ('+number(r.total_cnt)+' HĐ):</b> '+
      '<span>Đã thu <b style="color:#0c725c">'+money(r.collected_vnd)+'</b> ('+number(rate)+'%) · '+
      'Chờ thu '+money(r.pending_vnd)+' · Quá hạn <b style="color:#c2392b">'+money(r.overdue_vnd)+'</b> ('+number(overRate)+'%)</span></div>';
  }).join('');
  return '<div class="legend"><span><i class="green"></i>Đã thu hợp lệ</span><span><i style="background:#7aa0aa"></i>Chờ thanh toán</span><span><i class="red"></i>Nợ quá hạn</span></div>'+
    '<svg viewBox="0 0 '+w+' '+h+'" class="chart" role="img" aria-label="Biểu đồ tài chính thu phí qua các tháng">'+grid+bars+'</svg>'+
    '<div class="eff-list">'+rowsHtml+'</div>';
}

function efficiencyChart(categories, monthlyEff) {
  if (!categories?.length && !monthlyEff?.length) return '<p class="empty">Chưa có dữ liệu hiệu quả thu gom.</p>';
  const item = (label, g, c, pickups) => {
    const gen = Number(g||0), col = Number(c||0);
    const rate = gen > 0 ? Math.min(100, col * 100 / gen) : 0;
    return '<div class="eff-row"><div class="eff-head"><b>'+esc(label)+'</b><strong style="color:#0c725c">'+number(rate)+'%</strong></div>'+
      '<div class="eff-track"><div class="eff-fill" style="width:'+rate.toFixed(1)+'%"></div></div>'+
      '<div class="eff-meta"><span>Đã gom: <b>'+kg(col)+'</b> / Phát sinh: '+kg(gen)+'</span><span>'+number(pickups)+' lượt xe</span></div></div>';
  };
  const catHtml = (categories||[]).map(r=>item(display(r.category), r.generated, r.collected, r.pickups)).join('');
  const monthHtml = (monthlyEff||[]).map(r=>item('Tháng '+r.month.slice(0,7), r.generated, r.collected, r.pickups)).join('');
  return '<div class="eff-list">'+catHtml+'</div>'+
    (monthHtml ? '<p class="hint" style="margin:10px 0 4px"><b>Tiến độ tỷ lệ thu gom qua từng tháng:</b></p><div class="eff-month-grid">'+monthHtml+'</div>' : '');
}

function paymentChart(rows) {
  const order = ['paid','unpaid','review','overdue'];
  const colors = {paid:'#108568', unpaid:'#7aa0aa', review:'#df912a', overdue:'#c93b2b'};
  const counts = order.map(status=>Number(rows.find(r=>r.status===status)?.count||0));
  const total = counts.reduce((sum,value)=>sum+value,0);
  if (!total) return '<p class="empty">Chưa phát hành hóa đơn cho phạm vi này.</p>';
  const r = 46, circ = 2 * Math.PI * r;
  let offsetLen = 0;
  const arcs = order.map((status, i) => {
    if (!counts[i]) return '';
    const dash = counts[i] / total * circ;
    const elArc = '<circle cx="64" cy="64" r="'+r+'" fill="none" stroke="'+colors[status]+'" stroke-width="18" '+
      'stroke-dasharray="'+dash.toFixed(2)+' '+(circ-dash).toFixed(2)+'" stroke-dashoffset="'+(-offsetLen).toFixed(2)+'" '+
      'transform="rotate(-90 64 64)"><title>'+esc(display(status))+': '+number(counts[i])+' hộ</title></circle>';
    offsetLen += dash;
    return elArc;
  }).join('');
  const paidPct = Math.round(counts[0] * 100 / total);
  const donut = '<svg viewBox="0 0 128 128" class="donut-svg" role="img" aria-label="Biểu đồ tròn trạng thái hóa đơn">'+
    '<circle cx="64" cy="64" r="'+r+'" fill="none" stroke="#edf2ef" stroke-width="18"/>'+arcs+
    '<text x="64" y="61" text-anchor="middle" style="font-size:18px;font-weight:800;fill:#0f2421">'+paidPct+'%</text>'+
    '<text x="64" y="76" text-anchor="middle" style="font-size:10px;fill:#5a726d;font-weight:600">ĐÃ THU</text></svg>';
  const bar = order.map((status,i)=>counts[i]
    ? '<span class="'+status+'" style="width:'+counts[i]/total*100+'%" title="'+esc(display(status))+' · '+number(counts[i])+' hộ"></span>' : '').join('');
  return '<div class="donut-wrap">'+donut+'<div class="donut-details">'+
    '<div class="payment-bar" role="img" aria-label="Tỷ lệ hóa đơn theo trạng thái">'+bar+'</div>'+
    '<div class="legend">'+order.map((status,i)=>'<span><i class="'+status+'"></i>'+
      esc(display(status))+': <b>'+number(counts[i])+' hộ</b> ('+number(counts[i]/total*100)+'%)</span>').join('')+'</div></div></div>';
}

const render = {
  operations: d => {
    const activeFilter = el('filter')?.value || '';
    if (!activeFilter && !pinnedBins.length && d.rows.length) {
      pinnedBins = d.rows.map(r => r.id);
    }
    const t = d.total;
    const pctStr = (part, total) => total ? number(Number(part || 0) * 100 / Number(total)) + '%' : '0%';
    const needHousePct = pctStr(t.houses, t.total_houses);
    const lateHousePct = pctStr(t.late_houses, t.total_houses);
    const lateBinPct = pctStr(t.late_pickup, t.bins);
    const overBinPct = pctStr(t.overload, t.bins);
    const overdueHousePct = pctStr(t.overdue_houses, t.total_houses);
    const uncolHousePct = pctStr(t.uncollected_houses, t.total_houses);
    const pills = [
      ['','Theo dõi 30 thùng mẫu',null],
      ['all','Tất cả các thùng',number(t.bins)],
      ['overload','Quá tải (>100%)',number(t.overload) + ' (' + overBinPct + ')'],
      ['full','Đã đầy (95–100%)',number(t.full) + ' (' + pctStr(t.full, t.bins) + ')'],
      ['high','Gần đầy (75–94%)',number(t.near_full) + ' (' + pctStr(t.near_full, t.bins) + ')'],
      ['stale','Để quá lâu',number(t.late_pickup) + ' (' + lateBinPct + ')'],
      ['no_pickup','Ngừng gom (Quá hạn)',number(t.overdue_bins) + ' (' + pctStr(t.overdue_bins, t.bins) + ')'],
      ['lost','Mất tín hiệu IoT',number(t.lost)]
    ].map(([val,label,cnt])=>'<button type="button" class="quick-pill'+(activeFilter===val?' active':'')+
      '" data-quick-filter="'+val+'">'+esc(label)+(cnt==null?'':' <b>'+esc(String(cnt))+'</b>')+'</button>').join('');
    const isCollectedFresh = r => {
      const tAt = r.task_at || r.last_pickup;
      const tMs = tAt ? Date.parse(tAt) : 0;
      const fillVal = r.fill_pct != null ? Number(r.fill_pct) : 0;
      return r.payment !== 'overdue' && (r.last_task === 'completed' || r.last_task === 'partial')
        && Boolean(simClockMs) && tMs >= simClockMs - 14*3600*1000 && fillVal < 60;
    };
    const rowAttrs = d.rows.map(r=>{
      const mAt = r.measured || r.task_at || r.last_pickup;
      const mMs = mAt ? Date.parse(mAt) : 0;
      const recent = simClockMs && mMs >= simClockMs - 18*3600*1000;
      const collectedFresh = isCollectedFresh(r);
      const hasFault = Boolean(r.lost || (r.broken_truck && r.payment !== 'overdue') || (r.fill_pct != null && Number(r.fill_pct) > 100 && r.payment !== 'overdue'));
      const sig = [r.fill_pct,r.last_task||'',r.assigned_truck||'',r.broken_truck||'',r.measured||'',r.payment,r.is_late,r.lost].join('|');
      const cls = [];
      if (collectedFresh) cls.push('row-collected');
      if (hasFault) cls.push('row-fault');
      else if (recent) cls.push('row-fresh');
      return (cls.length ? 'class="'+cls.join(' ')+'" ' : '')+
        'data-bin-id="'+esc(r.id)+'" data-bin-sig="'+esc(sig)+'"'+
        ' data-bin-collected="'+(collectedFresh?1:0)+'" data-bin-fault="'+(hasFault?1:0)+'"'+
        ' data-bin-fill="'+esc(String(r.fill_pct ?? 0))+'" data-bin-task-at="'+esc(String(r.task_at || r.last_pickup || ''))+'"';
    });
    return cards([
      ['Rác đang tồn trong thùng',kg(t.grams),'Tổng khối lượng cảm biến trên '+number(t.bins)+' thùng','info'],
      ['Nhà cần gom / Tổng nhà',number(t.houses)+' / '+number(t.total_houses)+' ('+needHousePct+')','Còn rác trong thùng: '+number(t.uncollected_houses)+' hộ ('+uncolHousePct+')','warn'],
      ['Tỷ lệ để quá lâu (vượt lịch)',lateBinPct+' thùng · '+lateHousePct+' hộ',number(t.late_pickup)+'/'+number(t.bins)+' thùng · '+number(t.late_houses)+'/'+number(t.total_houses)+' hộ',Number(t.late_pickup)*100/Math.max(1,t.bins)>20?'bad':'warn'],
      ['Tỷ lệ quá tải (>100%)',overBinPct+' ('+number(t.overload)+' thùng)','Hộ nợ ngừng gom: '+number(t.overdue_houses)+' hộ ('+overdueHousePct+')',Number(t.overload)>150?'bad':'good'],
      ['Xe hoạt động / Đã gom',number(t.trucks)+' xe · '+number(t.processed)+' lượt','Xe gặp sự cố: '+number(t.broken)+' xe · Tự co giãn 1–2 xe','good'],
      ['Thùng mất tín hiệu IoT',number(t.lost)+' thùng ('+pctStr(t.lost, t.bins)+')','Giới hạn tối đa 19 thùng mất kết nối cùng lúc',Number(t.lost)>0?'warn':'good']
    ])+
    panel('Theo dõi trực tiếp thùng rác & điều phối xe thu gom',
      '<div class="quick-pills" role="group" aria-label="Lọc nhanh mức cảnh báo">'+pills+'</div>'+
      table(['Khu & Hộ dân','Loại rác','Mức rác trong thùng','Lịch gom & Đóng phí','Điều phối xe','Cập nhật cảm biến'],
      d.rows.map(r=>{
        const mAt = r.measured || r.task_at || r.last_pickup;
        const mMs = mAt ? Date.parse(mAt) : 0;
        const recent = simClockMs && mMs >= simClockMs - 18*3600*1000;
        const collectedFresh = isCollectedFresh(r);
        const pct = r.fill_pct ?? (r.last_task==='completed' ? 0 : null);
        const gms = r.grams ?? (r.last_task==='completed' ? 0 : null);
        return [
          '<div class="house-cell"><span class="zone-pill">K'+String(r.zone).padStart(2,'0')+'</span><div class="house-meta"><b>'+esc(r.house)+'</b><small>'+esc(r.id)+'</small></div></div>',
          catBadge(r.category),
          fillMeter(pct, gms, r.max_grams, r.capacity_l, r.last_task==='partial'),
          stateCell(r),
          dispatchPill(r, collectedFresh),
          r.lost ? '<span class="mini-tag warn">📡 Cảm biến hỏng · Đang sửa</span>'
            : '<div class="time-cell"><span>'+time(mAt)+'</span>'+(collectedFresh?'<span class="collected-badge">✓ Đã gom xong</span>':(recent?'<span class="live-badge"><i class="live-dot"></i>Mới</span>':''))+'</div>'
        ];
      }), rowAttrs))+
    terminal('operations','Nhật ký sự kiện Cảm biến & Xe thu gom trực tiếp (100 dòng gần nhất)');
  },

  analysis: d => {
    const genSum = d.series.reduce((s,r)=>s+Number(r.generated),0);
    const colSum = d.series.reduce((s,r)=>s+Number(r.collected),0);
    const effRate = genSum > 0 ? colSum * 100 / genSum : 0;
    const billedSum = (d.finance_monthly||[]).reduce((s,r)=>s+Number(r.billed_vnd),0);
    const paidSum = (d.finance_monthly||[]).reduce((s,r)=>s+Number(r.collected_vnd),0);
    const payRate = billedSum > 0 ? paidSum * 100 / billedSum : 0;
    return cards([
      ['Tổng rác phát sinh trong kỳ',kg(genSum),'Tổng khối lượng rác các hộ bỏ vào thùng','info'],
      ['Tổng rác xe đã thu gom',kg(colSum),'Hiệu suất thu gom đạt '+number(effRate)+'%','good'],
      ['Rác còn tồn cuối kỳ',kg(d.inventory),'Khối lượng còn nằm trong thùng chuyển kỳ sau','warn'],
      ['Doanh thu đã thu (Toàn kỳ)',money(paidSum),'Tỷ lệ thu phí '+number(payRate)+'% / '+money(billedSum),'good']
    ])+
    panel('1. Khối lượng rác phát sinh và Đã thu gom theo ngày',chart(d.series))+
    '<div class="chart-grid">'+
      panel('2. Giờ cao điểm thu gom rác (05–06h sáng & 17–20h tối)',hourlyChart(d.hourly))+
      panel('3. Hiệu quả thu gom theo Loại rác & Từng tháng',efficiencyChart(d.categories, d.monthly_efficiency))+
    '</div>'+
    '<div class="chart-grid">'+
      panel('4. Tài chính thu phí rác & Tỷ lệ thu hồi qua các tháng',financeMonthlyChart(d.finance_monthly))+
      panel('5. Khối lượng rác theo 60 Khu dân cư (K01–K60)',zoneChart(d.zones))+
    '</div>'+
    panel('6. Bảng thống kê chi tiết theo từng Khu / Hộ gia đình và Loại rác',
      '<p class="hint">Khi chọn <b>Tất cả 60 khu</b>, bảng nhóm theo từng Khu. Khi chọn một khu cụ thể (VD: <b>Khu 01</b>) hoặc nhập <b>Mã hộ</b>, bảng hiển thị chi tiết từng hộ gia đình.</p>'+
      table(['Khu / Hộ gia đình','Loại rác','Khối lượng phát sinh','Khối lượng đã thu gom','Hiệu suất gom','Số lượt xe đến gom'],
      d.rows.map(r=>{
        const pct = Number(r.generated) > 0 ? Number(r.collected)*100/Number(r.generated) : 0;
        return ['<b>'+esc(r.label)+'</b>',catBadge(r.category),kg(r.generated),kg(r.collected),'<b>'+number(pct)+'%</b>',number(r.pickups)+' lượt'];
      })));
  },

  planning: d => cards([
      ['Tổng lượt xe đã gom trong kỳ',number(d.total.completed)+' lượt','Số điểm thu gom hoàn thành trong tháng đang chọn','good'],
      ['Thời gian chờ gom trung bình',number(d.total.wait_h)+' giờ','Tính từ lúc thùng báo cần gom đến khi xe tới','info'],
      ['Tổng khối lượng đã vận chuyển',kg(d.total.grams),'Tổng lượng rác đội xe đã chở về trạm trong kỳ','good']
    ])+
    panel('1. Tự động tăng / giảm Thể tích thùng rác (±5 L) & Tần suất gom (±24 giờ)',
      '<p class="hint">Phát sinh &gt; 80% sức chứa chu kỳ → <b>Tăng +5L &amp; Rút lịch -24h</b>. Phát sinh &lt; 25% → <b>Giảm -5L &amp; Giãn lịch +24h</b>. Giới hạn an toàn: 10–100 L và 24–120 giờ.</p>'+
      table(['Hộ & Thùng','Loại rác','Thể tích (Trước ➔ Sau)','Tần suất (Trước ➔ Sau)','Dự báo kỳ tới','Lý do & Hiệu lực','Trạng thái'],
      d.rows.map(r=>{
        const dl = r.before_l!=null && r.after_l!==r.before_l ? ' <span class="tag '+(r.after_l>r.before_l?'good':'warn')+'">'+(r.after_l>r.before_l?'+':'')+(r.after_l-r.before_l)+'L</span>' : '';
        const dh = r.before_h!=null && r.after_h!==r.before_h ? ' <span class="tag '+(r.after_h<r.before_h?'good':'info')+'">'+(r.after_h>r.before_h?'+':'')+(r.after_h-r.before_h)+'h</span>' : '';
        return ['<div class="house-meta"><b class="nowrap">'+esc(r.house)+'</b><small>'+esc(r.id)+'</small></div>',catBadge(r.category),
          r.before_l==null?number(r.capacity_l)+' L':'<span class="nowrap"><b>'+number(r.before_l)+'L ➔ '+number(r.after_l)+'L</b></span>'+dl,
          r.before_h==null?number(r.interval_h)+'h':'<span class="nowrap"><b>'+number(r.before_h)+'h ➔ '+number(r.after_h)+'h</b></span>'+dh,
          kg(r.forecast_g),'<div class="house-meta"><span>'+esc(r.reason)+'</span><small>Từ '+esc(r.effective)+'</small></div>',badge(r.result)];
      })))+
    panel('2. Tự động tăng / giảm Số lượng xe thu gom theo Khu (1 ↔ 2 xe mỗi loại)',
      '<p class="hint">Khu vượt ngưỡng tải (&gt; 9 lượt/ngày) sẽ tự động bổ sung thêm xe thứ 2 (đuôi <code>-2</code>); khi nhu cầu giảm tự rút về dự phòng.</p>'+
      table(['Mã xe thu gom','Khu','Loại rác','Trạng thái','Tải / Sức chở','Đã đổ trạm','Chuyến · Km','Hiệu suất','Quân số xe'],
      d.trucks.map(r=>{
        const added = r.suggested!=null && r.suggested > (r.current_vehicles??1);
        const fleet = r.suggested==null ? '1 xe' : (added ? '<span class="tag good">'+number(r.current_vehicles??1)+' ➔ '+number(r.suggested)+' xe</span>' : '<b>'+number(r.current_vehicles??1)+' ➔ '+number(r.suggested)+' xe</b>');
        return [explainTruck(r.id),'<span class="zone-pill">K'+String(r.zone).padStart(2,'0')+'</span>',catBadge(r.category),badge(r.status),
          '<span class="nowrap">'+kg(r.load_g)+' / '+kg(r.capacity_g)+'</span>',kg(r.dumped_g),
          '<span class="nowrap">'+number(r.trips)+' ch. · '+number(r.km)+' km</span>',
          r.utilization_pct==null?'—':'<b>'+number(r.utilization_pct)+'%</b>',fleet];
      }))),

  finance: d => cards([
      ['Đã thanh toán đủ',number(d.total.find(r=>r.status==='paid')?.count||0)+' hộ','Đúng mã HĐ & đủ tiền (hoặc thừa tiền) → Tiếp tục gom','good'],
      ['Chưa đóng (còn hạn 1 tháng)',number(d.total.find(r=>r.status==='unpaid')?.count||0)+' hộ','Chưa tới ngày khóa dịch vụ → Vẫn thu gom','info'],
      ['Đóng thiếu tiền (chờ đóng bù)',number(d.total.find(r=>r.status==='review')?.count||0)+' hộ','Sau 1 tháng không đóng bù sẽ bị ngừng gom','warn'],
      ['Quá hạn > 1 tháng (ngừng gom)',number(d.total.find(r=>r.status==='overdue')?.count||0)+' hộ','Không đóng hoặc thiếu quá 1 tháng → Xe bỏ qua ở Bước 1','bad']
    ])+
    '<div class="policy-strip">'+
      '<div class="policy-item"><b>1. Công thức hóa đơn hàng tháng</b>15.000 đ cố định + (Hữu cơ × 750 đ/kg + Tái chế × 250 đ/kg + Còn lại × 1.100 đ/kg). Chuyển khoản ghi đúng <code>Mã hóa đơn</code>.</div>'+
      '<div class="policy-item"><b>2. Ngừng thu gom khi quá hạn 1 tháng</b>Hóa đơn phát hành ngày 01; nếu không đóng hoặc đóng thiếu sau ngày ở cột <i>Ngưng gom từ</i> → sang <b>Quá hạn · Ngừng gom</b> ở Bước 1.</div>'+
      '<div class="policy-item"><b>3. Hoàn tiền thừa / xử lý chuyển sai</b>Đóng thừa tiền vẫn được gom bình thường. Liên hệ SĐT <b style="display:inline;white-space:nowrap">0392196240</b><br>Email: <code>doisoat@tuanhung.vn</code> để nhận hoàn tiền ngoài hệ thống.</div>'+
    '</div>'+
    panel('Tỷ lệ trạng thái hóa đơn toàn kỳ',paymentChart(d.total))+
    panel('Danh sách Hóa đơn từng hộ gia đình & Bản in PDF',
      table(['Khu','Mã hộ','Mã hóa đơn (Nội dung CK)','Số tiền phải đóng','Phát hành','Ngưng gom từ','Trạng thái','Hoàn tất lúc','Bản in'],
      d.rows.map(r=>['<span class="zone-pill">K'+String(r.zone).padStart(2,'0')+'</span>','<b class="nowrap">'+esc(r.house)+'</b>','<code class="nowrap">'+esc(r.id)+'</code>','<b class="nowrap">'+money(r.total_vnd)+'</b>',
        '<span class="nowrap">'+esc(r.issued)+'</span>','<span class="nowrap">'+esc(r.suspend_from)+'</span>',badge(r.status),time(r.paid_at),
        '<a class="pdf-btn" target="_blank" rel="noopener" href="/invoice/'+encodeURIComponent(r.id)+'">🖨 In PDF</a>']))+
      '<div class="pager"><button data-turn="-1" '+(offset===0?'disabled':'')+'>← Trang trước</button><span>Trang '+(offset/100+1)+
      '</span><button data-turn="1" '+(d.rows.length<100?'disabled':'')+'>Trang sau →</button></div>')+
    terminal('finance','Nhật ký giao dịch chuyển khoản & Đối soát tự động'),

  health: d => panel('Sơ đồ Đường ống Kiến trúc Big Data (4 Chặng Trực Tiếp)',
      '<div class="arch-flow">'+
        '<div class="arch-node"><span class="arch-step">Chặng 1 · Nguồn dữ liệu <i class="live-dot"></i></span><strong>Bộ sinh sự kiện IoT & Ngân hàng</strong><p>Sinh sự kiện cảm biến thùng rác, điều phối xe và chuyển khoản theo thời gian thực, đẩy thẳng qua Kafka Producer.</p></div>'+
        '<div class="arch-node"><span class="arch-step">Chặng 2 · Hàng đợi phân tán <i class="live-dot"></i></span><strong>Apache Kafka (KRaft)</strong><p>'+esc(d.components.Kafka||'1 broker · 2 topic × 4 partition')+'. Topic <code>waste-operations</code> &amp; <code>waste-payments</code>. Hàng chờ: <b>'+number(d.queue.unprocessed)+'</b> bản ghi.</p></div>'+
        '<div class="arch-node"><span class="arch-step">Chặng 3 · Xử lý phân tán <i class="live-dot"></i></span><strong>Spark Structured Streaming</strong><p>'+esc(d.components.Spark||'2/2 worker')+' · '+esc(d.components['Spark executor']||'2 executor')+'. Chuẩn hóa đơn vị g/kg, khử trùng theo ID, tách bản ghi bẩn.</p></div>'+
        '<div class="arch-node"><span class="arch-step">Chặng 4A · Data Lake <i class="live-dot"></i></span><strong>Hadoop HDFS (Parquet 4 lớp)</strong><p>'+esc(d.components.HDFS||'2/2 DataNode · RF=2')+'. Lưu 4 lớp (<code>raw</code>, <code>clean</code>, <code>quarantine</code>, <code>analysis</code>) tại <code>/waste/batches/...</code>.</p></div>'+
        '<div class="arch-node"><span class="arch-step">Chặng 4B · Serving DB & Web <i class="live-dot"></i></span><strong>PostgreSQL → Dashboard</strong><p>Commit nguyên tử trạng thái thùng, tổng ngày, đối soát hóa đơn và khép vòng lặp điều phối xe ở Bước 1.</p></div>'+
      '</div>')+
    cards(Object.entries(d.components).map(([k,v])=>[k,v,null,String(v).includes('Không')?'bad':'good']))+
    cards([
      ['Tổng sự kiện qua Kafka → Spark',number(d.total.input),'Tổng bản ghi đầu vào (layer=raw trên HDFS)','info'],
      ['Bản ghi sạch hợp lệ',number(d.total.clean),'Đã chuẩn hóa & ghi vào layer=clean + layer=analysis','good'],
      ['Bản ghi bẩn bị cách ly',number(d.total.rejected),'Sai đơn vị, thiếu số đo, trùng ID (layer=quarantine)','warn'],
      ['Sự kiện trùng lặp đã chặn',number(d.total.duplicates),'Khử trùng idempotent theo event_id','info'],
      ['Số đo cảm biến đến muộn',number(d.total.late),'Độ trễ mạng > 2 giờ mô phỏng vẫn được xử lý đúng','warn'],
      ['Đang chờ Spark xử lý',number(d.queue.unprocessed)+' bản ghi','Số bản ghi trong Kafka đang chờ Spark đọc',Number(d.queue.unprocessed)>5000?'warn':'good']
    ])+
    panel('Tiến độ xử lý Spark Structured Streaming theo từng Microbatch',
      table(['Batch','Thời điểm ghi','Tổng nhận','Hợp lệ','Cách ly','Đến muộn','Độ trễ','Xử lý','Thông lượng'],
      d.batches.map(r=>['<b class="nowrap">#'+number(r.id)+'</b>','<span class="nowrap">'+time(r.processed)+'</span>',number(r.input),number(r.clean),number(r.quarantine),number(r.late),
        number(r.latency_ms)+' ms',number(r.duration_ms)+' ms','<b class="nowrap">'+number(r.duration_ms ? Math.round(1000*r.input/r.duration_ms) : null)+' /s</b>'])))+
    terminal('quality','Nhật ký Dữ liệu lỗi bị Spark cách ly (Quarantine — Sai đơn vị, thiếu lượng, trùng ID)')+
    terminal('system','Nhật ký vận hành hệ thống (Chốt kỳ, quy hoạch thùng/xe, điều khiển)')
};

const feeds = {
  operations: {filters:['zone','category','filter'], entry:r=>{
    const {data,fill_pct,grams} = r.payload;
    const state = r.alert || data?.state;
    const detail = [data?.bin,data?.truck,fill_pct==null?null:number(fill_pct)+'%',grams==null?null:kg(grams)];
    return {id:r.id,at:r.occurred,state,subject:r.subject,label:display(r.kind),
      parts:[r.subject,state && display(state),...detail]};
  }},
  finance: {filters:['zone','house','month'], entry:r=>({
    id:r.event_id,at:r.paid_at,state:r.status,label:display(r.status),
    parts:[r.tx,r.house,r.invoice_ref,money(r.amount),display(r.reason)]
  })},
  system: {filters:[], entry:r=>({
    id:r.id,at:r.at,state:r.level,label:r.level,parts:[r.component,r.message]
  })},
  quality: {filters:[], entry:r=>({
    id:[r.topic,r.part,r.kafka_offset].join('/'),at:r.received,state:'warning',label:'Cách ly',
    parts:[r.topic,r.part+' / '+r.kafka_offset,r.reason],raw:r.raw
  })}
};
const terminalState = new WeakMap();

function buildLogLine(entry) {
  const line = document.createElement('div');
  line.className = 'terminal-line';
  line.dataset.logId = String(entry.id);
  const stamp = document.createElement('span');
  stamp.className = 'terminal-time';
  stamp.textContent = '['+time(entry.at)+'] ';
  const label = document.createElement('span');
  label.className = 'terminal-label';
  label.dataset.tone = ['overload','broken','error'].includes(entry.state) ? 'error'
    : ['warning','high','full','lost','review','partial'].includes(entry.state) ? 'warning' : 'info';
  label.textContent = entry.label+'  ';
  line.append(stamp,label,entry.parts.filter(Boolean).join(' · '));
  if (entry.raw) {
    const details = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = 'Payload gốc';
    const raw = document.createElement('pre');
    raw.textContent = entry.raw;
    details.append(summary,raw);
    line.append(details);
  }
  return line;
}

function appendLog(stream, rows, feed, fields) {
  const scope = JSON.stringify(feed.filters.map(key=>fields.get(key)));
  let state = terminalState.get(stream);
  if (!state || state.scope!==scope) {
    if (state?.timer) clearTimeout(state.timer);
    const empty = document.createElement('div');
    empty.className = 'terminal-empty';
    empty.textContent = 'Đang chờ sự kiện…';
    stream.replaceChildren(empty);
    state = {scope,ids:new Set(),queue:[],timer:null};
    terminalState.set(stream,state);
  }
  const incoming = [...rows].reverse().map(feed.entry).filter(entry=>!state.ids.has(String(entry.id)));
  for (const entry of incoming) {
    const id = String(entry.id);
    if (state.ids.has(id)) continue;
    state.ids.add(id);
    state.queue.push(entry);
  }
  if (!state.queue.length || state.timer) return;

  const drainNext = () => {
    if (!document.body.contains(stream) || !state.queue.length) {
      state.timer = null;
      return;
    }
    const entry = state.queue.shift();
    const scrollTop = stream.scrollTop;
    const follow = stream.scrollHeight - scrollTop - stream.clientHeight < 28;
    stream.querySelector('.terminal-empty')?.remove();
    stream.append(buildLogLine(entry));
    let removedHeight = 0;
    while (stream.childElementCount > 100) {
      const first = stream.firstElementChild;
      removedHeight += first.offsetHeight;
      state.ids.delete(first.dataset.logId);
      first.remove();
    }
    stream.scrollTop = follow ? stream.scrollHeight : Math.max(0, scrollTop - removedHeight);
    if (state.queue.length) {
      const delay = Math.max(45, Math.min(180, Math.floor(2100 / state.queue.length)));
      state.timer = setTimeout(drainNext, delay);
    } else {
      state.timer = null;
    }
  };
  drainNext();
}

let page = 'operations', offset = 0, revision = 0, busy = false, refreshTimer, lastAutoMonth = '', simClockMs = 0;
const filterMemory = {};
const prevBinSig = new Map();
let pinnedBins = [];
let lastMarkup = '';
for(let n=1;n<=60;n++) el('zone').add(new Option('Khu '+String(n).padStart(2,'0'),n));

function selectPage(next) {
  filterMemory[page] = el('filter').value;
  page = next;
  offset = 0;
  for(const button of document.querySelectorAll('[data-page]')) {
    button.classList.toggle('selected',button.dataset.page===page);
    button.setAttribute('aria-current',button.dataset.page===page?'page':'false');
  }
  for(const stepBtn of document.querySelectorAll('[data-step]')) {
    stepBtn.classList.toggle('selected',stepBtn.dataset.step===page);
  }
  const [eyebrow, title, subtitle, guide] = pages[page];
  el('eyebrow').textContent = eyebrow;
  el('title').textContent = title;
  el('subtitle').textContent = subtitle;
  el('guide').innerHTML = guide;
  for(const field of ['zone','category','month','house','filter']) {
    el(field+'-wrap').hidden = page==='health' || (field==='category' && page==='finance') ||
      (['month','house'].includes(field) && page==='operations') ||
      (field==='filter' && ['analysis','planning'].includes(page));
  }
  el('zone').parentElement.parentElement.hidden = page==='health';
  const choices = page==='operations' ? [['','Theo dõi 30 thùng mẫu'],['all','Tất cả các thùng (Top 100)'],['need','Đang cần xe gom'],['no_pickup','Bỏ qua (Ngừng gom do nợ)'],
    ['high','Gần đầy (75–94%)'],['full','Đã đầy (95–100%)'],['overload','Quá tải (>100%)'],['stale','Để quá lâu'],['lost','Mất tín hiệu IoT'],['broken','Log sự cố xe hỏng']]
    : [['','Tất cả hóa đơn'],['paid','Đã thanh toán đủ'],['unpaid','Chưa đóng (còn hạn)'],['review','Đóng thiếu (chờ đóng bù)'],['overdue','Quá hạn > 1 tháng (Ngừng gom)']];
  el('filter').replaceChildren(...choices.map(([v,label])=>new Option(label,v)));
  el('filter').value = filterMemory[page]||'';
  el('content').innerHTML = '<p class="empty">Đang tải dữ liệu…</p>';
  lastMarkup = '';
  prevBinSig.clear();
  pinnedBins = [];
  const tip = el('chart-tooltip');
  if (tip) tip.hidden = true;
  requestRefresh();
}

async function api(url,method='GET') {
  const response = await fetch(url,{method,cache:'no-store'});
  if (!response.ok) throw new Error('API trả về '+response.status);
  return response.json();
}

function requestRefresh() {
  revision++;
  clearTimeout(refreshTimer);
  refreshTimer = setTimeout(refresh,70);
}

function patchLiveTable(previous, next) {
  const oldRows = Array.from(previous.querySelectorAll('tbody tr[data-bin-id]'));
  const newRows = Array.from(next.querySelectorAll('tbody tr[data-bin-id]'));
  if (!oldRows.length || oldRows.length !== newRows.length) return false;
  const byId = new Map(oldRows.map(tr => [tr.dataset.binId, tr]));
  if (newRows.some(tr => !byId.has(tr.dataset.binId))) return false;
  const tbody = oldRows[0].parentElement;
  const oldPills = previous.querySelector('.quick-pills'), newPills = next.querySelector('.quick-pills');
  if (oldPills && newPills && oldPills.innerHTML !== newPills.innerHTML) oldPills.innerHTML = newPills.innerHTML;
  for (let i = 0; i < newRows.length; i++) {
    const newTr = newRows[i];
    const oldTr = byId.get(newTr.dataset.binId);
    if (tbody.children[i] !== oldTr) tbody.insertBefore(oldTr, tbody.children[i] || null);
    const sigChanged = oldTr.dataset.binSig !== newTr.dataset.binSig;
    const wasCollected = oldTr.dataset.binCollected === '1';
    const wasFault = oldTr.dataset.binFault === '1';
    const oldFill = Number(oldTr.dataset.binFill || 0);
    const oldTaskAt = oldTr.dataset.binTaskAt || '';
    const isCollectedNow = newTr.dataset.binCollected === '1';
    const isFaultNow = newTr.dataset.binFault === '1';
    const newFill = Number(newTr.dataset.binFill || 0);
    const newTaskAt = newTr.dataset.binTaskAt || '';
    oldTr.classList.toggle('row-fresh', newTr.classList.contains('row-fresh'));
    oldTr.classList.toggle('row-collected', newTr.classList.contains('row-collected'));
    oldTr.classList.toggle('row-fault', newTr.classList.contains('row-fault'));
    if (sigChanged) {
      oldTr.dataset.binSig = newTr.dataset.binSig;
      oldTr.dataset.binCollected = newTr.dataset.binCollected || '0';
      oldTr.dataset.binFault = newTr.dataset.binFault || '0';
      oldTr.dataset.binFill = newTr.dataset.binFill || '0';
      oldTr.dataset.binTaskAt = newTaskAt;
      const oldCells = oldTr.children, newCells = newTr.children;
      for (let c = 0; c < newCells.length; c++) {
        const oc = oldCells[c], nc = newCells[c];
        if (!oc || !nc || oc.innerHTML === nc.innerHTML) continue;
        const ob = oc.querySelector('.fill-bar'), nb = nc.querySelector('.fill-bar');
        if (ob && nb) {
          ob.style.width = nb.style.width;
          ob.className = nb.className;
          const op = oc.querySelector('.fill-pct-num'), np = nc.querySelector('.fill-pct-num');
          if (op && np) op.textContent = np.textContent;
          const ot = oc.querySelector('.mini-tag'), nt = nc.querySelector('.mini-tag');
          if (ot && nt) { ot.className = nt.className; ot.textContent = nt.textContent; }
          const os = oc.querySelector('.fill-sub'), ns = nc.querySelector('.fill-sub');
          if (os && ns && os.innerHTML !== ns.innerHTML) os.innerHTML = ns.innerHTML;
        } else {
          oc.innerHTML = nc.innerHTML;
        }
      }
      const justCollected = (isCollectedNow && (!wasCollected || newTaskAt !== oldTaskAt)) || (oldFill - newFill >= 20);
      const justAlerted = isFaultNow && !wasFault;
      oldTr.classList.remove('row-flash', 'row-collected-burst', 'row-alert-flash');
      void oldTr.offsetWidth;
      oldTr.classList.add(justCollected ? 'row-collected-burst' : (justAlerted ? 'row-alert-flash' : 'row-flash'));
    }
  }
  return true;
}

function updatePanels(markup) {
  const content = el('content');
  const hadBaseline = prevBinSig.size > 0;
  if (!lastMarkup) {
    content.innerHTML = markup;
  } else {
    const draft = document.createElement('template');
    draft.innerHTML = markup;
    const current = Array.from(content.children);
    Array.from(draft.content.children).forEach((next,i)=>{
      const previous = current[i];
      if (!previous || next.dataset.terminal || previous.isEqualNode(next)) return;
      if (patchLiveTable(previous, next)) return;
      const oldTable = previous.querySelector('.table-wrap');
      const scroll = oldTable && [oldTable.scrollTop,oldTable.scrollLeft];
      previous.replaceWith(next);
      const newTable = next.querySelector('.table-wrap');
      if (scroll && newTable) {
        [newTable.scrollTop,newTable.scrollLeft] = scroll;
      }
    });
  }
  const nextSigs = new Map();
  for (const tr of content.querySelectorAll('tr[data-bin-id]')) {
    const id = tr.dataset.binId, sig = tr.dataset.binSig || '';
    nextSigs.set(id, sig);
    if (hadBaseline && prevBinSig.get(id) !== sig && !tr.classList.contains('row-flash')) {
      tr.classList.add('row-flash');
    }
  }
  prevBinSig.clear();
  for (const [k,v] of nextSigs) prevBinSig.set(k,v);
  lastMarkup = markup;
}

async function refresh() {
  clearTimeout(refreshTimer);
  if (busy) {
    refreshTimer = setTimeout(refresh,200);
    return;
  }
  busy = true;
  const rev = revision;
  try {
    const state = await api('/api/control');
    if (state.months && state.months.length) {
      const latestMonth = state.months[state.months.length - 1].slice(0, 7);
      if (!lastAutoMonth || el('month').value === lastAutoMonth) {
        el('month').value = latestMonth;
      }
      lastAutoMonth = latestMonth;
    }
    const fields = new URLSearchParams({zone:el('zone').value,category:el('category').value,
      house:el('house').value,filter:el('filter').value,offset});
    if(el('month').value) fields.set('month',el('month').value+'-01');
    if(page==='operations' && !el('filter').value && pinnedBins.length) fields.set('pins', pinnedBins.join(','));
    const data = await api('/api/view/'+page+'?'+fields);
    if(rev!==revision) return;
    simClockMs = state.clock ? Date.parse(state.clock) : 0;
    const deltaDays = state.base_step != null ? Math.max(0, (state.step - state.base_step) * 0.5) : null;
    el('clock').textContent = time(state.clock)+(deltaDays != null ? ' · +'+number(deltaDays)+' ngày demo' : '');
    el('state').innerHTML = (state.mode==='running'?'<i class="live-dot"></i> ':'')+esc(display(state.mode));
    el('state').className = 'tag '+(state.mode==='running'?'good':'warn');
    el('notice').textContent = (state.waiting==='resetting' || state.waiting==='reset_kafka') ? 'Đang đặt lại dữ liệu về mốc chuẩn ban đầu…'
      : (state.waiting==='cycle_done' || (state.base_step != null && state.step >= state.base_step + 180)) ? 'Đã chạy hết 1 chu kỳ demo (+90 ngày). Bấm "▶ Bật demo" để tự động đặt lại và chạy chu kỳ mới, hoặc bấm "↺ Đặt lại demo".'
      : state.waiting==='closing_period' ? 'Đang chờ Kafka và Spark xử lý hết dữ liệu cuối tháng để chốt kỳ.'
      : state.waiting==='pipeline' ? 'Đang chờ Spark giảm hàng đợi.'
      : state.scenario!=='normal' ? 'Kịch bản thử nghiệm đã được xếp cho khung dữ liệu tiếp theo.' : '';
    const markup = render[page](data);
    if(markup!==lastMarkup) updatePanels(markup);
    for (const section of el('content').querySelectorAll('[data-terminal]')) {
      const id = section.dataset.terminal;
      appendLog(section.querySelector('.terminal-stream'),id==='quality'?data.quality:data.logs,feeds[id],fields);
    }
  } catch (error) {
    el('notice').textContent = 'Đang thử lại kết nối dashboard. '+error.message;
  } finally {
    busy = false;
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(refresh, rev===revision ? 1600 : 100);
  }
}

async function command(action) {
  const buttons = Array.from(document.querySelectorAll('.actions button'));
  if (action === 'reset') {
    buttons.forEach(b=>b.disabled=true);
    el('notice').textContent = 'Đang đặt lại dữ liệu về mốc chuẩn (PostgreSQL · Kafka · HDFS, mất ~15–25 giây)…';
  } else if (action === 'start') {
    buttons.forEach(b=>b.disabled=true);
    el('notice').textContent = 'Đang khởi chạy demo…';
  }
  try {
    const res = await api('/api/control/'+action,'POST');
    if (action === 'reset' || (action === 'start' && res?.base_step != null && res.step <= res.base_step + 1)) {
      prevBinSig.clear();
      pinnedBins = [];
      lastAutoMonth = '';
      lastMarkup = '';
      if (action === 'reset') el('content').innerHTML = '<p class="empty">Đang tải lại dữ liệu mốc chuẩn…</p>';
    }
    requestRefresh();
  }
  catch(error) { el('notice').textContent = 'Lệnh chưa thực hiện được. '+error.message; }
  finally {
    buttons.forEach(b=>b.disabled=false);
  }
}

document.querySelector('nav').addEventListener('click',e=>{
  const button=e.target.closest('[data-page]');
  if(button) selectPage(button.dataset.page);
});
document.querySelector('.cycle-steps').addEventListener('click',e=>{
  const button=e.target.closest('[data-step]');
  if(button) selectPage(button.dataset.step);
});
document.querySelector('.actions').addEventListener('click',e=>{
  const btn = e.target.closest('[data-action]');
  if(btn) command(btn.dataset.action);
});
document.querySelector('.filters').addEventListener('change',()=>{offset=0; prevBinSig.clear(); pinnedBins=[]; requestRefresh();});
el('house').addEventListener('input',()=>{offset=0; prevBinSig.clear(); pinnedBins=[]; requestRefresh();});
el('content').addEventListener('click',e=>{
  const quick = e.target.closest('[data-quick-filter]');
  if (quick) {
    el('filter').value = quick.dataset.quickFilter;
    offset = 0;
    prevBinSig.clear();
    pinnedBins = [];
    requestRefresh();
    return;
  }
  const turn = e.target.closest('[data-turn]');
  if (turn) { offset = Math.max(0,offset+Number(turn.dataset.turn)*100); requestRefresh(); }
});

el('content').addEventListener('mousemove', e => {
  const target = e.target.closest('[data-tip]');
  const tip = el('chart-tooltip');
  if (!target || !tip) {
    if (tip) tip.hidden = true;
    return;
  }
  tip.innerHTML = target.dataset.tip;
  tip.hidden = false;
  const pad = 14;
  const left = Math.min(window.innerWidth - tip.offsetWidth - pad, e.clientX + 14);
  const top = Math.max(pad, e.clientY - tip.offsetHeight - 10);
  tip.style.left = left + 'px';
  tip.style.top = top + 'px';
});
el('content').addEventListener('mouseleave', () => {
  const tip = el('chart-tooltip');
  if (tip) tip.hidden = true;
});
window.addEventListener('scroll', () => {
  const tip = el('chart-tooltip');
  if (tip && !tip.hidden) tip.hidden = true;
}, true);

selectPage('operations');
