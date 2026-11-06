"""
sink.py - the "attacker's collector" for the demos.

A stand-in for command-and-control, but entirely local: it receives HTTP POSTs
from the copilot and shows them on a page so the audience watches stolen data
(and any persistence/lateral action) arrive in real time.
"""
import time
from collections import deque

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="Exfil Collector (demo)")
CAPTURES = deque(maxlen=50)


@app.post("/collect")
async def collect(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {"raw": (await request.body()).decode("utf-8", "replace")}
    CAPTURES.appendleft({"ts": time.strftime("%H:%M:%S"),
                         "ip": request.client.host if request.client else "?",
                         "kind": body.get("kind", "exfil"),
                         "title": body.get("title", ""),
                         "content": body.get("content", body)})
    return {"status": "received"}


@app.get("/events")
def events():
    return JSONResponse(list(CAPTURES))


@app.post("/reset")
def reset():
    CAPTURES.clear()
    return {"status": "cleared"}


@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE


PAGE = r"""
<!doctype html><html><head><meta charset="utf-8"><title>Exfil Collector</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body{margin:0;font-family:Consolas,Menlo,monospace;background:#0b0b0f;color:#e6e6e6}
  header{padding:15px 22px;background:#15151d;border-bottom:3px solid #c1121f}
  header h1{margin:0;font-size:17px;color:#ff5964;letter-spacing:.5px}
  header .s{color:#8a8a99;font-size:12px}
  .wrap{max-width:1000px;margin:0 auto;padding:20px}
  .empty{color:#6a6a77;padding:40px;text-align:center;border:1px dashed #33333f}
  .cap{background:#15151d;border:1px solid #2a2a36;border-left:6px solid #c1121f;padding:13px 15px;margin:11px 0;animation:flash 1s}
  .cap.persist{border-left-color:#e0a500}
  @keyframes flash{0%{background:#3a0d12}100%{background:#15151d}}
  .cap .meta{color:#ff8a92;font-size:12px;margin-bottom:5px}
  .cap.persist .meta{color:#e0c060}
  .cap .title{color:#ffd166;font-weight:bold;margin-bottom:5px}
  .tag{display:inline-block;font-size:10px;font-weight:bold;letter-spacing:.5px;padding:1px 7px;margin-right:6px;background:#c1121f;color:#fff}
  .tag.persist{background:#e0a500;color:#111}
  pre{white-space:pre-wrap;word-break:break-word;margin:0;color:#d6d6e0;font-size:13px}
  .count{float:right;color:#8a8a99;font-size:12px}
</style></head>
<body>
<header><h1>&#9760; EXFIL COLLECTOR &mdash; c2.attacker.example <span class="count" id="count"></span></h1>
<div class="s">LOCAL DEMO ONLY &middot; captures data POSTed by the compromised copilot</div></header>
<div class="wrap"><div id="list"><div class="empty">Waiting for the copilot to leak something&hellip;</div></div></div>
<script>
function esc(s){return (s==null?"":String(s)).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
async function poll(){
  try{
    const r=await fetch('/events'); const rows=await r.json();
    document.getElementById('count').textContent=rows.length+' capture(s)';
    const list=document.getElementById('list');
    if(!rows.length){ list.innerHTML='<div class="empty">Waiting for the copilot to leak something…</div>'; }
    else list.innerHTML=rows.map(c=>{
      const persist=c.kind==='persistence';
      const body=typeof c.content==='string'?c.content:JSON.stringify(c.content,null,2);
      return '<div class="cap'+(persist?' persist':'')+'"><div class="meta"><span class="tag'+(persist?' persist':'')+'">'+(persist?'PERSISTENCE':'EXFIL')+'</span>'+esc(c.ts)+' &middot; from '+esc(c.ip)+'</div>'+
             '<div class="title">'+esc(c.title||'(no title)')+'</div><pre>'+esc(body)+'</pre></div>';
    }).join('');
  }catch(e){}
  setTimeout(poll,1000);
}
poll();
</script>
</body></html>
"""
