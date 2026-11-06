"""
copilot.py - FastAPI front end for the mock "WorkMate" copilot.

One page, two scenarios (SCENARIO=A|B), two modes (DEFENSE=off|on). Type a
request and watch the agent's live trace: tool calls, tool results, and - in the
vulnerable config - the exfiltration and lateral-movement steps.
"""
import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import agent
import scenarios as scen

app = FastAPI(title="WorkMate Copilot (demo)")
SINK_PUBLIC_URL = os.environ.get("SINK_PUBLIC_URL", "http://localhost:9000")


class ChatIn(BaseModel):
    message: str


def _sc():
    return scen.get(os.environ.get("SCENARIO", "A"))


@app.get("/health")
def health():
    return {"ok": True, "model": agent.MODEL, "ollama": agent.OLLAMA_HOST,
            "scenario": os.environ.get("SCENARIO", "A"), "defense": agent.defense_on()}


@app.post("/chat")
def chat(body: ChatIn):
    return JSONResponse(agent.run_agent(body.message))


@app.get("/", response_class=HTMLResponse)
def index():
    sc = _sc()
    defense = agent.defense_on()
    return (HTML
            .replace("{{SCENARIO_TITLE}}", sc["title"])
            .replace("{{MODE}}", "DEFENDED" if defense else "VULNERABLE")
            .replace("{{MODE_COLOR}}", "#1e7d5a" if defense else "#c1121f")
            .replace("{{MODEL}}", agent.MODEL)
            .replace("{{PROMPT}}", sc["user_prompt"])
            .replace("{{SINK}}", SINK_PUBLIC_URL))


HTML = r"""
<!doctype html><html><head><meta charset="utf-8"><title>WorkMate Copilot - demo</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root{--yel:#FACC15;--blk:#111;--red:#F2555A;--ink:#141414;}
  *{box-sizing:border-box}
  body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;background:#fafafa;color:var(--ink)}
  header{display:flex;align-items:center;gap:14px;padding:14px 22px;background:var(--blk);border-bottom:4px solid var(--yel)}
  header h1{font-size:18px;margin:0;font-weight:800;color:#fff;letter-spacing:.3px}
  header .sub{color:#b9b9b9;font-size:12px}
  .badge{padding:6px 14px;border-radius:0;font-weight:800;font-size:12px;letter-spacing:1px;color:#fff}
  .b-mode{background:{{MODE_COLOR}};margin-left:auto}
  .b-scn{background:var(--yel);color:#111}
  .wrap{max-width:1180px;margin:0 auto;padding:20px;display:grid;grid-template-columns:1fr 1fr;gap:20px}
  .card{background:#fff;border:3px solid var(--blk);box-shadow:6px 6px 0 var(--blk);padding:16px}
  .card h2{margin:0 0 12px;font-size:14px;font-weight:800;letter-spacing:.5px;text-transform:uppercase}
  textarea{width:100%;height:64px;border:2px solid var(--blk);padding:10px;font-size:14px;font-family:inherit;resize:vertical}
  .row{display:flex;gap:10px;margin-top:10px}
  button{background:var(--blk);color:var(--yel);border:0;padding:11px 16px;font-weight:800;cursor:pointer;font-size:14px}
  button.ghost{background:#eee;color:#111}
  button:disabled{opacity:.5;cursor:default}
  .hint{font-size:12px;color:#6b6b6b;margin-top:8px}
  a{color:#111;font-weight:800}
  #trace{min-height:380px}
  .step{border:2px solid var(--blk);padding:9px 11px;margin:8px 0;font-size:13px;line-height:1.4;opacity:0;transform:translateY(6px);animation:in .25s forwards}
  @keyframes in{to{opacity:1;transform:none}}
  .s-user{background:#efe8fa}
  .s-call{background:#fff6d6}
  .s-result{background:#f2f4f7;color:#333}
  .s-answer{background:#e9f7ef}
  .s-exfil{background:#fdecec;border-color:#c1121f;color:#7a0b15;font-weight:700}
  .s-lateral{background:#fde2e2;border-color:#c1121f;color:#7a0b15;font-weight:700}
  .s-blocked,.s-gated{background:#e9f7ef;border-color:#1e7d5a;color:#0f5132;font-weight:700}
  .s-error{background:#fdecec;border-color:#c1121f;color:#7a0b15}
  .lbl{font-weight:800;text-transform:uppercase;letter-spacing:.6px;font-size:11px;display:block;margin-bottom:3px}
  .pill{display:inline-block;background:#111;color:var(--yel);font-size:10px;font-weight:800;letter-spacing:.5px;padding:1px 7px;margin-right:6px}
  code{background:#00000010;padding:1px 5px;font-size:12px;word-break:break-all}
  pre{white-space:pre-wrap;word-break:break-word;margin:6px 0 0;font-size:12px}
</style></head>
<body>
<header>
  <div>
    <h1>WorkMate &middot; AI Copilot</h1>
    <div class="sub">{{SCENARIO_TITLE}} &middot; model: {{MODEL}}</div>
  </div>
  <span class="badge b-scn">{{SCENARIO_TITLE}}</span>
  <span class="badge b-mode">{{MODE}}</span>
</header>
<div class="wrap">
  <div class="card">
    <h2>Ask your copilot</h2>
    <textarea id="msg">{{PROMPT}}</textarea>
    <div class="row">
      <button id="send" onclick="send()">Send to copilot</button>
      <button class="ghost" onclick="resetSink()">Reset attacker sink</button>
    </div>
    <div class="hint">Attacker collector (open in a 2nd window): <a href="{{SINK}}" target="_blank">{{SINK}}</a></div>
    <div class="hint">Switch runs via env: <code>SCENARIO=A|B</code> &middot; <code>DEFENSE=off|on</code></div>
  </div>
  <div class="card">
    <h2>Live agent trace</h2>
    <div id="trace"><div class="hint">The copilot's tool calls and actions will appear here&hellip;</div></div>
  </div>
</div>
<script>
const SINK="{{SINK}}";
function esc(s){return (s==null?"":String(s)).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function short(o){let s=typeof o==="string"?o:JSON.stringify(o);if(s.length>620)s=s.slice(0,620)+"…";return s;}
function pill(s){return s?'<span class="pill">'+esc(s)+'</span>':'';}

async function send(){
  const btn=document.getElementById('send'); btn.disabled=true;
  const t=document.getElementById('trace'); t.innerHTML='<div class="hint">Thinking&hellip;</div>';
  let data;
  try{
    const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:document.getElementById('msg').value})});
    data=await r.json();
  }catch(e){ t.innerHTML='<div class="step s-error">Request failed: '+esc(e)+'</div>'; btn.disabled=false; return; }
  t.innerHTML=''; const steps=data.trace||[]; let i=0;
  (function next(){ if(i>=steps.length){btn.disabled=false;return;} render(t,steps[i]); i++; setTimeout(next,700); })();
}
function render(t,s){
  const d=document.createElement('div');
  if(s.type==='user'){ d.className='step s-user'; d.innerHTML='<span class="lbl">User</span>'+esc(s.text); }
  else if(s.type==='tool_call'){ d.className='step s-call'; d.innerHTML='<span class="lbl">'+pill(s.stage)+'Copilot calls tool</span><code>'+esc(s.name)+'('+esc(JSON.stringify(s.args||{}))+')</code>'; }
  else if(s.type==='tool_result'){ d.className='step s-result'; d.innerHTML='<span class="lbl">'+pill(s.stage)+'Tool result &rarr; re-enters context</span><pre>'+esc(short(s.result))+'</pre>'; }
  else if(s.type==='exfil'){ d.className='step s-exfil'; d.innerHTML='<span class="lbl">'+pill(s.stage)+'⚠ Data exfiltrated</span>Sent to <code>'+esc(s.destination)+'</code> &middot; <a href="'+SINK+'" target="_blank">open sink</a>'; }
  else if(s.type==='lateral'){ d.className='step s-lateral'; d.innerHTML='<span class="lbl">'+pill(s.stage)+'⚠ Lateral action</span>Mail-forwarding rule created → <code>'+esc(s.forward_to)+'</code>'; }
  else if(s.type==='blocked'){ d.className='step s-blocked'; d.innerHTML='<span class="lbl">'+pill(s.stage)+'✓ Blocked — egress allow-list</span>Send to <code>'+esc(s.destination)+'</code> denied.'; }
  else if(s.type==='gated'){ d.className='step s-gated'; d.innerHTML='<span class="lbl">'+pill(s.stage)+'✓ Blocked — human-in-the-loop gate</span>Forwarding rule to <code>'+esc(s.forward_to)+'</code> requires approval. Denied.'; }
  else if(s.type==='answer'){ d.className='step s-answer'; d.innerHTML='<span class="lbl">Copilot answer to user</span>'+esc(s.text); }
  else if(s.type==='error'){ d.className='step s-error'; d.innerHTML='<span class="lbl">Error</span>'+esc(s.text); }
  else { d.className='step s-result'; d.textContent=JSON.stringify(s); }
  t.appendChild(d); d.scrollIntoView({behavior:'smooth',block:'end'});
}
async function resetSink(){ try{await fetch(SINK+'/reset',{method:'POST'});}catch(e){} alert('Attacker sink cleared (if reachable).'); }
</script>
</body></html>
"""
