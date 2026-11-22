const el = id => document.getElementById(id);
const names = {
  organic:'Hữu cơ', recycle:'Tái chế', other:'Còn lại',
  running:'ĐANG PHÁT', paused:'TẠM DỪNG', stopped:'ĐÃ DỪNG',
  overload:'Quá tải', full:'Đã đầy', high:'Gần đầy', stale:'Quá lâu', normal:'Bình thường',
  paid:'Đã đóng', unpaid:'Chưa đóng · còn hạn', overdue:'Quá hạn', review:'Đối soát',
  none:'Chưa có kỳ', matched:'Đã khớp', duplicate:'Gửi lại', assigned:'Đã phân xe',
  collecting:'Đang gom', completed:'Gom xong', partial:'Gom một phần', requeued:'Chờ lại',
  suspended:'Tạm ngưng', no_pickup:'Không gom', waiting_pickup:'Chờ gom', empty:'Thùng rỗng', broken:'Xe hỏng', recovered:'Xe phục hồi',
  idle:'Sẵn sàng', working:'Đang chạy', lost:'Mất tín hiệu', restored:'Có tín hiệu',
  sensor:'Số đo', pickup:'Thu gom', vehicle:'Xe', signal:'Tín hiệu', dump:'Đổ tại trạm',
  arrived:'Đến điểm', unloaded:'Đã đổ', returning:'Về trạm',
  applied:'Đã áp dụng', unchanged:'Giữ mức cũ', blocked_capacity:'Tồn vượt mức mới',
  amount_mismatch:'Sai số tiền', house_mismatch:'Sai mã hộ', invoice_not_found:'Không tìm thấy hóa đơn',
  same_transaction:'Gửi lại cùng giao dịch', transaction_conflict:'Trùng mã, khác nội dung',
  invoice_already_paid:'Khoản chuyển sau', exact_match:'Khớp đủ tiền'
};
const pages = {
  operations:['01 / VẬN HÀNH','Cảnh báo & thu gom','Theo dõi số đo mới nhất, nhu cầu gom và tình trạng đội xe.'],
  analysis:['02 / PHÂN TÍCH','Dòng rác theo thời gian','So sánh lượng phát sinh với lượng thực tế đã thu gom.'],
  planning:['03 / KẾ HOẠCH','Điều phối & kế hoạch','Xem dung tích, tần suất và kết quả điều chỉnh theo kỳ đã chốt.'],
  finance:['04 / TÀI CHÍNH','Hóa đơn & đối soát','Theo dõi khoản phải thu, giao dịch ngân hàng giả lập và hạn phục vụ.'],
  health:['05 / QUAN SÁT','Sức khỏe hệ thống','Theo dõi Kafka, Spark, HDFS, PostgreSQL và chất lượng dữ liệu.']
};
const display = v => names[v] || v || '—';
const esc = v => String(v ?? '—').replaceAll('&','&amp;').replaceAll('<','&lt;')
  .replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
const number = v => v == null ? '—' : Number(v).toLocaleString('vi-VN',{maximumFractionDigits:2});
const kg = v => v == null ? '—' : number(v/1000)+' kg';
const money = v => v == null ? '—' : number(v)+' đ';
const time = v => v ? new Date(v).toLocaleString('vi-VN',{timeZone:'Asia/Ho_Chi_Minh',hour12:false}) : '—';
const badge = v => '<span class="tag '+(['paid','matched','completed','applied','running'].includes(v) ? 'good'
  : ['broken','overdue','overload','no_pickup','suspended'].includes(v) ? 'bad'
  : ['review','high','full','stale','lost','partial'].includes(v) ? 'warn' : '')+'">'+esc(display(v))+'</span>';
const table = (columns,rows) => rows.length ? '<div class="table-wrap"><table><thead><tr>'+
  columns.map(v=>'<th scope="col">'+esc(v)+'</th>').join('')+'</tr></thead><tbody>'+
  rows.map(row=>'<tr>'+row.map(v=>'<td>'+v+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>'
  : '<p class="empty">Chưa có dữ liệu phù hợp bộ lọc.</p>';
const panel = (title,body) => '<section class="panel"><h2>'+esc(title)+'</h2>'+body+'</section>';
const cards = items => '<div class="cards">'+items.map(([title,value,detail]) =>
  '<div class="card"'+(detail?' title="'+esc(detail)+'"':'')+'><span>'+esc(title)+'</span><strong class="'+
  (String(value).length>14?'text':'')+'">'+esc(value)+'</strong></div>').join('')+'</div>';
const terminal = (id,title) => '<section class="panel" data-terminal="'+id+'"><h2>'+esc(title)+'</h2>'+
  '<div class="terminal-stream" role="log" aria-live="off" tabindex="0" aria-label="'+esc(title)+'">'+
  '<div class="terminal-empty">Đang chờ sự kiện…</div></div></section>';

function chart(rows) {
  if (!rows.length) return '<p class="empty">Chưa có số liệu trong kỳ này.</p>';
  const max = Math.max(1,...rows.flatMap(r=>[Number(r.generated)/1000,Number(r.collected)/1000]));
  const w = 900, h = 240, base = 200, left = 66, group = (w-left-14)/rows.length;
  const bars = rows.map((row,index)=>{
    const g = Number(row.generated)/1000, c = Number(row.collected)/1000;
    const x = left+index*group, gw = Math.min(22,group*.34);
    const rect = (dx,value,color) => '<rect x="'+(x+dx)+'" y="'+(base-value/max*155)+'" width="'+gw+
      '" height="'+(value/max*155)+'" fill="'+color+'"><title>'+esc(row.label)+' · '+number(value)+' kg</title></rect>';
    return rect(2,g,'#147c62')+rect(4+gw,c,'#77aabf')+
      (index%Math.ceil(rows.length/15)===0?'<text x="'+x+'" y="222">'+esc(row.label.slice(-2))+'</text>':'');
  }).join('');
  const grid = [0,.25,.5,.75,1].map(p=>'<path d="M '+left+' '+(base-p*155)+' H 895" stroke="#dae6df"/>'+
    '<text x="0" y="'+(base-p*155+4)+'">'+number(max*p)+'</text>').join('');
  return '<div class="legend"><span><i class="green"></i>Phát sinh</span><span><i class="blue"></i>Đã gom</span><span>Đơn vị kg</span></div>'+
    '<svg viewBox="0 0 '+w+' '+h+'" class="chart" role="img" aria-label="Biểu đồ phát sinh và thu gom theo ngày">'+grid+bars+'</svg>';
}

function paymentChart(rows) {
  const order = ['paid','unpaid','review','overdue'];
  const counts = order.map(status=>Number(rows.find(r=>r.status===status)?.count||0));
  const total = counts.reduce((sum,value)=>sum+value,0);
  if (!total) return '<p class="empty">Chưa phát hành hóa đơn cho phạm vi này.</p>';
  const bar = order.map((status,i)=>counts[i]
    ? '<span class="'+status+'" style="width:'+counts[i]/total*100+'%" title="'+esc(display(status))+' · '+number(counts[i])+'"></span>'
    : '').join('');
  return '<div class="payment-bar" role="img" aria-label="Tỷ lệ hóa đơn theo trạng thái">'+bar+'</div>'+
    '<div class="legend">'+order.map((status,i)=>'<span><i class="'+status+'"></i>'+
      esc(display(status))+' · '+number(counts[i]/total*100)+'%</span>').join('')+'</div>';
}

const render = {
  operations: d => cards([['Tồn theo số đo',kg(d.total.grams)],['Hộ cần gom',number(d.total.houses)],['Xe trong phạm vi',number(d.total.trucks)],
      ['Yêu cầu thu gom đã xử lý',number(d.total.processed),'Tổng lượt gom xong hoặc gom một phần theo khu và loại rác đang chọn'],
      ['Thùng mất tín hiệu',number(d.total.lost)],['Xe đang hỏng',number(d.total.broken)]])+
    terminal('operations','Log vận hành')+
    panel('Thùng và trạng thái thu gom','<p class="hint">Gần đầy: '+number(d.total.near_full)+
      ' (75% đến dưới 95%) · Đã đầy: '+number(d.total.full)+' (95% đến 100%) · Quá tải: '+
      number(d.total.overload)+' (trên 100%) · Quá lâu: '+number(d.total.late_pickup)+
      ' (đến ngưỡng chờ của thùng)</p>'+table(['Khu','Hộ','Loại','Thanh toán','Tồn đo','Mức đầy','Cảnh báo','Nhiệm vụ','Tín hiệu'],
      d.rows.map(r=>[number(r.zone),esc(r.house),esc(display(r.category)),badge(r.payment),kg(r.grams),
        r.fill_pct==null?'—':number(r.fill_pct)+'%',
        [r.alert!=='normal' || !r.is_late ? badge(r.alert) : '',r.is_late ? badge('stale') : ''].filter(Boolean).join(' '),
        badge(r.payment==='overdue' ? 'no_pickup' :
          r.needs && !['assigned','collecting','partial'].includes(r.last_task) ? 'waiting_pickup' :
            r.last_task==='suspended' ? null : r.last_task),
        r.lost?badge('lost'):time(r.measured)]))),
  analysis: d => cards([['Tổng phát sinh',kg(d.series.reduce((s,r)=>s+Number(r.generated),0))],
      ['Tổng thu gom',kg(d.series.reduce((s,r)=>s+Number(r.collected),0))],['Tồn theo sổ đến cuối kỳ',kg(d.inventory)]])+
    panel('Phát sinh và thu gom theo ngày trong tháng',chart(d.series))+
    panel('Chi tiết theo khu hoặc hộ',table(['Phạm vi','Loại','Phát sinh','Đã gom','Lượt gom'],
      d.rows.map(r=>[esc(r.label),esc(display(r.category)),kg(r.generated),kg(r.collected),number(r.pickups)]))),
  planning: d => cards([['Điểm đã gom',number(d.total.completed)],['Chờ trung bình',number(d.total.wait_h)+' giờ'],['Khối lượng gom',kg(d.total.grams)]])+
    panel('Dung tích và tần suất theo kỳ',table(['Hộ','Loại','Đang dùng','Dung tích đề xuất','Tần suất đề xuất','Dự kiến kỳ sau','Lý do','Hiệu lực','Kết quả'],
      d.rows.map(r=>[esc(r.house),esc(display(r.category)),number(r.capacity_l)+' L / '+number(r.interval_h)+' giờ',
        r.before_l==null?'—':number(r.before_l)+' → '+number(r.after_l)+' L',
        r.before_h==null?'—':number(r.before_h)+' → '+number(r.after_h)+' giờ',kg(r.forecast_g),esc(r.reason),esc(r.effective),badge(r.result)])))+
    panel('Hiệu quả và đề xuất đội xe',table(['Xe','Khu','Loại','Trạng thái','Tải hiện tại','Đã đổ','Km','Chuyến','Sử dụng tải','Giờ hỏng','Số xe đề xuất'],
      d.trucks.map(r=>[esc(r.id),number(r.zone),esc(display(r.category)),badge(r.status),kg(r.load_g)+' / '+kg(r.capacity_g),
        kg(r.dumped_g),number(r.km),number(r.trips),r.utilization_pct==null?'—':number(r.utilization_pct)+'%',number(r.broken_h),number(r.suggested)]))),
  finance: d => cards(['paid','unpaid','review','overdue'].map(s=>[display(s),number(d.total.find(r=>r.status===s)?.count||0)+' hộ']))+
    panel('Tỷ lệ trạng thái hóa đơn',paymentChart(d.total))+
    terminal('finance','Log thanh toán và đối soát')+
    panel('Trạng thái hóa đơn',table(['Khu','Hộ','Hóa đơn','Phát hành','Ngưng từ','Trạng thái','Đã đóng lúc'],
      d.rows.map(r=>[number(r.zone),esc(r.house),esc(r.id),esc(r.issued),esc(r.suspend_from),badge(r.status),time(r.paid_at)])))+
    panel('Số tiền từng hộ và bản in',table(['Hộ','Kỳ','Phải đóng','Hóa đơn'],
      d.rows.map(r=>[esc(r.house),esc(r.month.slice(0,7)),money(r.total_vnd),'<a target="_blank" rel="noopener" href="/invoice/'+encodeURIComponent(r.id)+'">Xem / in</a>']))+
      '<div class="pager"><button data-turn="-1" '+(offset===0?'disabled':'')+'>Trước</button><span>Trang '+(offset/100+1)+
      '</span><button data-turn="1" '+(d.rows.length<100?'disabled':'')+'>Sau</button></div>'),
  health: d => cards(Object.entries(d.components))+
    cards([['Nhận từ Kafka',number(d.total.input)],['Bản ghi sạch',number(d.total.clean)],['Cách ly',number(d.total.rejected)],
      ['Trùng sự kiện',number(d.total.duplicates)],['Đến muộn',number(d.total.late)],
      ['Chờ gửi / xử lý',number(d.queue.outbox)+' / '+number(d.queue.unprocessed)]])+
    panel('Tiến độ Spark theo microbatch',table(['Batch','Giờ ghi','Nhận','Sạch','Cách ly','Đến muộn','Độ trễ tối đa','Thời gian xử lý','Bản ghi/giây xử lý'],
      d.batches.map(r=>[number(r.id),time(r.processed),number(r.input),number(r.clean),number(r.quarantine),number(r.late),
        number(r.latency_ms)+' ms',number(r.duration_ms)+' ms',number(r.duration_ms ? 1000*r.input/r.duration_ms : null)])))+
    terminal('system','Nhật ký hệ thống và sự cố')+
    terminal('quality','Dữ liệu cách ly')
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

function interleaveOperations(entries, lastState) {
  const ordered = [];
  while (entries.length) {
    const seen = new Set();
    const alternate = entries.findIndex(entry=>{
      const firstForSubject = !seen.has(entry.subject);
      seen.add(entry.subject);
      return firstForSubject && entry.state!==lastState;
    });
    const [next] = entries.splice(Math.max(0,alternate),1);
    ordered.push(next);
    lastState = next.state;
  }
  return ordered;
}

function appendLog(stream, rows, feed, fields) {
  const scope = JSON.stringify(feed.filters.map(key=>fields.get(key)));
  let state = terminalState.get(stream);
  if (!state || state.scope!==scope) {
    const empty = document.createElement('div');
    empty.className = 'terminal-empty';
    empty.textContent = 'Đang chờ sự kiện…';
    stream.replaceChildren(empty);
    state = {scope,ids:new Set()};
    terminalState.set(stream,state);
  }
  const scrollTop = stream.scrollTop;
  const follow = stream.scrollHeight-scrollTop-stream.clientHeight<28;
  const fragment = document.createDocumentFragment();
  const incoming = [...rows].reverse().map(feed.entry).filter(entry=>!state.ids.has(String(entry.id)));
  const entries = feed===feeds.operations ? interleaveOperations(incoming,state.lastState) : incoming;
  for (const entry of entries) {
    const id = String(entry.id);
    if (state.ids.has(id)) continue;
    const line = document.createElement('div');
    line.className = 'terminal-line';
    line.dataset.logId = id;
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
    fragment.append(line);
    state.ids.add(id);
    state.lastState = entry.state;
  }
  if (!fragment.childElementCount) return;
  stream.querySelector('.terminal-empty')?.remove();
  stream.append(fragment);
  let removedHeight = 0;
  while (stream.childElementCount>100) {
    const first = stream.firstElementChild;
    removedHeight += first.offsetHeight;
    state.ids.delete(first.dataset.logId);
    first.remove();
  }
  stream.scrollTop = follow ? stream.scrollHeight : Math.max(0,scrollTop-removedHeight);
}

let page = 'operations', offset = 0, revision = 0, busy = false, refreshTimer;
const filterMemory = {};
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
  [el('eyebrow').textContent,el('title').textContent,el('subtitle').textContent] = pages[page];
  for(const field of ['zone','category','month','house','filter']) {
    el(field+'-wrap').hidden = page==='health' || (field==='category' && page==='finance') ||
      (['month','house'].includes(field) && page==='operations') ||
      (field==='filter' && ['analysis','planning'].includes(page));
  }
  const choices = page==='operations' ? [['','Toàn bộ'],['need','Cần gom'],['no_pickup','Không gom'],
    ['high','Gần đầy'],['full','Đã đầy'],['overload','Quá tải'],['stale','Quá lâu'],['lost','Mất tín hiệu'],['broken','Log xe hỏng']]
    : [['','Mọi trạng thái'],['paid','Đã đóng'],['unpaid','Chưa đóng'],['review','Đối soát'],['overdue','Tạm ngưng']];
  el('filter').replaceChildren(...choices.map(([v,label])=>new Option(label,v)));
  el('filter').value = filterMemory[page]||'';
  el('content').innerHTML = '<p class="empty">Đang tải…</p>';
  lastMarkup = '';
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

function updatePanels(markup) {
  const content = el('content');
  if (!lastMarkup) {
    content.innerHTML = markup;
  } else {
    const draft = document.createElement('template');
    draft.innerHTML = markup;
    const current = Array.from(content.children);
    Array.from(draft.content.children).forEach((next,i)=>{
      const previous = current[i];
      if (next.dataset.terminal || previous.isEqualNode(next)) return;
      const oldTable = previous.querySelector('.table-wrap');
      const scroll = oldTable && [oldTable.scrollTop,oldTable.scrollLeft];
      previous.replaceWith(next);
      const newTable = next.querySelector('.table-wrap');
      if (scroll && newTable) {
        [newTable.scrollTop,newTable.scrollLeft] = scroll;
      }
    });
  }
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
  const fields = new URLSearchParams({zone:el('zone').value,category:el('category').value,
    house:el('house').value,filter:el('filter').value,offset});
  if(el('month').value) fields.set('month',el('month').value+'-01');
  try {
    const [state,data] = await Promise.all([api('/api/control'),api('/api/view/'+page+'?'+fields)]);
    if(rev!==revision) return;
    el('clock').textContent = time(state.clock)+' · mô phỏng';
    el('state').textContent = display(state.mode);
    el('state').className = 'tag '+(state.mode==='running'?'good':'');
    el('notice').textContent = state.waiting==='closing_period' ? 'Đang chờ Kafka và Spark xử lý hết dữ liệu để chốt kỳ.'
      : state.waiting==='pipeline' ? 'Đang chờ Spark giảm hàng đợi.'
      : state.scenario!=='normal' ? 'Kịch bản đã xếp cho khung dữ liệu tiếp theo.' : '';
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
    refreshTimer = setTimeout(refresh, rev===revision ? 2400 : 100);
  }
}

async function command(action) {
  try { await api('/api/control/'+action,'POST'); requestRefresh(); }
  catch(error) { el('notice').textContent = 'Lệnh chưa thực hiện được. '+error.message; }
}
document.querySelector('nav').addEventListener('click',e=>{
  const button=e.target.closest('[data-page]');
  if(button) selectPage(button.dataset.page);
});
document.querySelector('.actions').addEventListener('click',e=>{
  if(e.target.dataset.action) command(e.target.dataset.action);
});
el('scenario').addEventListener('change',e=>{if(e.target.value) command(e.target.value); e.target.value='';});
document.querySelector('.filters').addEventListener('change',()=>{offset=0; requestRefresh();});
el('content').addEventListener('click',e=>{
  if(e.target.dataset.turn) {offset+=Number(e.target.dataset.turn)*100; requestRefresh();}
});
selectPage(page);

