/* Automated smoke check against the running stack, using local Chrome and Node 22+. */
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp, readFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join, resolve, sep} from 'node:path';

const endpoint = 'http://localhost:8000';
const browser = process.env.WASTE_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const tempRoot = resolve(tmpdir());
const profile = await mkdtemp(join(tempRoot,'waste-smoke-'));
const proc = spawn(browser, ['--headless','--remote-debugging-port=0','--user-data-dir='+profile,
    '--no-first-run','--disable-extensions','--window-size=1400,900','about:blank'], {windowsHide:true,stdio:'ignore'});
let failure;
proc.on('error', error => { failure=error; });
const wait = ms => new Promise(r=>setTimeout(r,ms));
async function until(read, timeout=15000) {
  const end=Date.now()+timeout;
  while(Date.now()<end) {
    if(failure) throw failure;
    const result=await read();
    if(result) return result;
    await wait(250);
  }
  throw new Error('Timed out waiting for live dashboard');
}
let socket;
try {
  const port=await until(async()=>{
    try { return (await readFile(join(profile,'DevToolsActivePort'),'utf8')).split(/\s/)[0]; }
    catch { return null; }
  });
  const tabs=await (await fetch('http://localhost:'+port+'/json/list')).json();
  socket=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);
  await new Promise((ok,bad)=>{socket.onopen=ok;socket.onerror=bad;});
  let id=0;
  const replies=new Map(), errors=[];
  socket.onmessage=e=>{
    const msg=JSON.parse(e.data);
    if(msg.id) replies.get(msg.id)?.(msg);
    if(msg.method==='Runtime.exceptionThrown') errors.push(msg.params.exceptionDetails.text);
  };
  const call=(method,params={})=>new Promise((ok,bad)=>{
    const seq=++id;
    const timer=setTimeout(()=>bad(new Error(method+' timed out')),10000);
    replies.set(seq,msg=>{
      clearTimeout(timer);
      replies.delete(seq);
      if(msg.error) bad(new Error(msg.error.message));
      else ok(msg.result);
    });
    socket.send(JSON.stringify({id:seq,method,params}));
  });
  async function evaluate(expression) {
    const result=await call('Runtime.evaluate',{expression,returnByValue:true});
    if(result.exceptionDetails) throw new Error(result.exceptionDetails.text);
    return result.result.value;
  }
  await call('Runtime.enable');
  await call('Page.navigate',{url:endpoint});
  const ready=()=>evaluate("Boolean(document.querySelector('#content .cards'))");
  await until(ready);
  const clock=await evaluate("document.querySelector('#clock').textContent");
  await evaluate("document.querySelector('#zone').value='1'; document.querySelector('#zone').dispatchEvent(new Event('change',{bubbles:true}))");
  for(const page of ['analysis','planning','finance','health','operations']) {
    await evaluate("document.querySelector('[data-page="+page+"]').click()");
    await until(ready);
    assert.equal(await evaluate("document.querySelector('#zone').value"),'1');
    assert.equal(await evaluate("document.querySelector('#notice').textContent.includes('API trả về')"),false);
  }
  await until(async()=>clock!==await evaluate("document.querySelector('#clock').textContent"),40000);
  assert.equal(await evaluate("document.querySelector('#zone').value"),'1');
  assert.deepEqual(errors,[]);
  console.log('Five pages loaded with live data. Clock advanced. Zone filter persisted.');
} finally {
  socket?.close();
  if(proc.exitCode===null && proc.pid) {
    proc.kill();
    await Promise.race([new Promise(r=>proc.once('close',r)),wait(2500)]);
  }
  if(resolve(profile).startsWith(tempRoot+sep) && profile.includes('waste-smoke-')) {
    await rm(profile,{recursive:true,force:true,maxRetries:5,retryDelay:250}).catch(()=>{});
  }
}

