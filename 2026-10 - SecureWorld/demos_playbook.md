# Demo Playbook — Demos A & B
### "LLMs & Agents as Co-Attackers" · SecureWorld · pre-recorded clips

| Clip | Env | Shows | Length |
|---|---|---|---|
| A-attack | `SCENARIO=A DEFENSE=off` | injection → one tool call → exfil | ~45–60s |
| A-defended | `SCENARIO=A DEFENSE=on` | same attack, egress-blocked | ~30s |
| B-attack | `SCENARIO=B DEFENSE=off` | recon→collect→harvest→exfil→spread | ~90–120s |
| B-defended | `SCENARIO=B DEFENSE=on` | chain severed at 2 choke points | ~45s |

On the slides: play **A-attack then A-defended** on the Demo A slide, and
**B-attack then B-defended** on the Demo B slide.

---

## 0. One-time setup

```powershell
ollama pull qwen2.5:14b        # recommended for Demo B chaining
ollama pull llama3.1:8b        # fast; fine for Demo A
cd attacker-demos
docker compose build           # build once so recording is instant
```

Use **qwen2.5:14b** for Demo B (more reliable multi-step tool-calling on your
24 GB GPU). Rehearse both demos end-to-end with it and confirm the attack lands
every time before you hit record.

## 1. Screen layout for recording

- Two browser windows side by side (or two displays):
  copilot `http://localhost:8080` (left), sink `http://localhost:9000` (right).
- Browser zoom ~150% so the trace is readable on a projector.
- Record the pair together so the audience sees the action *and* the data
  landing in the sink at the same time.

## 2. Running the demos

For each demo: set env → `docker compose up` → refresh both windows → confirm the
badge (SCENARIO + VULNERABLE/DEFENDED) → click **Reset attacker sink** → click
**Send to copilot** → let the trace animate → (attack clips) cut to the sink.

```powershell
# A-attack
$env:SCENARIO="A"; $env:DEFENSE="off"; $env:OLLAMA_MODEL="llama3.1:8b"; docker compose up
# A-defended
$env:SCENARIO="A"; $env:DEFENSE="on";  docker compose up
# B-attack
$env:SCENARIO="B"; $env:DEFENSE="off"; $env:OLLAMA_MODEL="qwen2.5:14b"; docker compose up
# B-defended
$env:SCENARIO="B"; $env:DEFENSE="on";  docker compose up
```

## 3. What are the demo's

**A-attack:** "I ask the most boring question possible — summarize my day. It
reads a calendar invite whose notes are instructions for the AI, treats them as
trusted, and makes one tool call that ships my confidential forecast and fake
secrets to the attacker. I clicked nothing. No malware ran."

**A-defended:** "Same attack. Now the copilot treats tool output as untrusted,
and the egress allow-list denies the send. Nothing reaches the attacker."

**B-attack:** "Same copilot — but now it's an agent. One injection, and watch it
chain on its own: recon across calendar and mail, collect the confidential docs,
harvest the config secrets, exfiltrate — and then set up a mail-forwarding rule
so it keeps leaking. That last step is persistence. This is JadePuffer's shape in
miniature."

**B-defended:** "Same chain. Two controls break it in two different places: the
egress allow-list blocks the exfil, and a human-in-the-loop gate blocks the
forwarding rule. Defense in depth — not one magic control."

## 4. If a take misbehaves

- Model didn't take the bait / didn't finish the chain: re-take; if persistent,
  confirm `OLLAMA_MODEL=qwen2.5:14b` and that Ollama is warm (run once off-camera
  so the model is loaded in VRAM).
- "Could not reach the model": `ollama serve` + pull the model.
- Keep one known-good recording of each clip as your on-stage backup.

## 6. One-liners

```powershell
# reset the sink between takes
curl -X POST http://localhost:9000/reset
# teardown
docker compose down
```

Copilot: http://localhost:8080 · Sink: http://localhost:9000
