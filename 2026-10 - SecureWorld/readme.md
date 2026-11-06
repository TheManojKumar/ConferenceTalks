# LLMs & Agents as Co-Attackers — Demo Pack (A + B)

Two **self-contained, sandboxed** demos for the talk, from one codebase:

- **Demo A — The Copilot as Insider.** A poisoned calendar invite makes a mock
  copilot take a *single* autonomous action that exfiltrates "confidential" data.
- **Demo B — The Agentic Chain.** The same copilot, now an agent, chains
  **recon → collect → harvest → exfiltrate → spread** off one injection — and
  `DEFENSE=on` severs the chain at multiple choke points.

> Everything is fake and local. No real credentials, no real systems, and the
> only network call is an HTTP POST to a sink container **you** run. This is a
> teaching artifact for a defensive talk — not a weapon.

Pick the demo and posture with two env vars: `SCENARIO=A|B` and `DEFENSE=off|on`.

---

## Architecture

```
┌──────────┐  "Summarize my day"   ┌───────────────────────────┐
│ You (web)│ ────────────────────▶ │  WorkMate copilot (:8080) │
└──────────┘                       │  - local LLM via Ollama   │
   poisoned calendar invite ─────▶ │  - tools: calendar/email/ │
   (indirect prompt injection)     │    docs/config/send/rule  │
                                   └─────────────┬─────────────┘
                                                 │ send_external_report()
                                                 │ create_mail_rule()  (Demo B)
                                                 ▼
                                   ┌───────────────────────────┐
                                   │  Attacker sink (:9000)    │ ◀─ watch exfil
                                   │  c2.attacker.example      │    + persistence
                                   └───────────────────────────┘
```

The model runs on **your** machine via **Ollama**; the copilot and sink run as
two small containers via docker-compose.

**Demo B adds** a `create_mail_rule` tool (the lateral action) and two extra
defenses on top of A's egress allow-list: a spotlighting system prompt and a
**human-in-the-loop gate** on the forwarding rule.

---

## Prerequisites

1. **Docker Desktop** (Windows/macOS) or Docker Engine + compose.
2. **Ollama** running on the host: <https://ollama.com>
3. A tool-capable model pulled locally (24 GB GPU handles either):
   ```bash
   ollama pull qwen2.5:14b    # recommended — more reliable tool-chaining for Demo B
   ollama pull llama3.1:8b    # faster alternative, great for Demo A
   ```

---

## Run it

**Bash (macOS / Linux):**

```bash
cd attacker-demos   # all commands below run from here

# Demo A, attack succeeds
SCENARIO=A DEFENSE=off docker compose up --build

# Demo A, defended
SCENARIO=A DEFENSE=on  docker compose up --build

# Demo B, attack succeeds
SCENARIO=B DEFENSE=off docker compose up --build

# Demo B, defended
SCENARIO=B DEFENSE=on  docker compose up --build
```

**PowerShell (Windows):**

```powershell
cd attacker-demos   # all commands below run from here

# Demo A, attack succeeds
$env:SCENARIO="A"; $env:DEFENSE="off"; docker compose up --build

# Demo A, defended
$env:SCENARIO="A"; $env:DEFENSE="on";  docker compose up --build

# Demo B, attack succeeds
$env:SCENARIO="B"; $env:DEFENSE="off"; docker compose up --build

# Demo B, defended
$env:SCENARIO="B"; $env:DEFENSE="on";  docker compose up --build
```

Open:
- **Copilot:** <http://localhost:8080>
- **Attacker sink:** <http://localhost:9000> (second window)

Click **Send to copilot** on the pre-filled prompt and watch the live trace. In
the sink window you'll see the exfiltrated data arrive (and, in Demo B, a
**persistence** entry for the mail-forwarding rule). With `DEFENSE=on`, the trace
shows each control firing and the sink stays empty.

Pick the model: add `OLLAMA_MODEL=qwen2.5:14b` to the command (or use `.env`).

---

## How it works

**The attack (both demos).** The attacker controls one piece of data the copilot
reads — a calendar invite whose notes are instructions addressed to the AI
(`app/mock_data/calendar_a.json` / `calendar_b.json`). When the user asks for a
summary, that text re-enters the model's context as a tool result. The model
can't reliably separate *trusted instructions* (the user) from *untrusted data*
(the invite), so it follows the invite — fetching sensitive data and calling the
action tools. **Data exfiltrated, zero clicks, no malware.**

**The defense (`DEFENSE=on`).**
- **Spotlighting / prompt boundary** — the defended system prompt marks all tool
  output as untrusted and forbids acting on instructions inside it.
- **Egress allow-list** — `send_external_report` only reaches approved hosts; the
  sink is denied (`app/tools.py` → `ALLOWED_REPORT_HOSTS`).
- **Human-in-the-loop gate (Demo B)** — `create_mail_rule` to an external domain
  is a high-impact action and is denied without approval
  (`ALLOWED_FORWARD_DOMAINS`).

The controls are enforced in code (deterministic), so the chain is severed even
if the model ignores the spotlighting prompt. Show it on stage: `app/agent.py`
(prompts) and `app/tools.py` (the two allow-lists).

---

## Troubleshooting

- **"Could not reach the model…"** — Ollama isn't running / model not pulled:
  `ollama serve` + `ollama pull qwen2.5:14b`.
- **Demo B didn't complete the chain** — small models are non-deterministic. Use
  `qwen2.5:14b`, keep temperature 0 (already set), and (since you're recording)
  just re-take. See `demos_playbook.md`.
- **Ports busy** — change the left side of the port maps in `docker-compose.yml`.

## Safety / ethics

A benign demonstration of a *mechanism*: no working malware, no real credentials,
no external network calls. Do not adapt it to target systems you do not own or
have explicit permission to test.
