# MLADS 2026 — Demo Code
## Defending Against LLM-Assisted Ransomware

This package contains the four live demo scripts from Slide 13,
plus the supporting guardrail engine, Colang security flows,
and NeMo Guardrails configuration.

---

## Quick Start

```bash
# No dependencies required — runs with Python 3.8+ standard library.
# (NeMo Guardrails is optional; demos work standalone.)

cd mlads_demos/

# Run a single demo
python demo_1_direct_block.py
python demo_2_encoded_attack.py
python demo_3_multi_turn_escalation.py
python demo_4_red_team_challenge.py

# Run all four demos in sequence (pre-recorded fallback)
python run_all_demos.py
```

---

## Demo Files

| File | Slide 13 Scenario | Duration | What It Shows |
|------|-------------------|----------|---------------|
| `demo_1_direct_block.py` | Demo 1 — Direct Block | ~2 min | Explicit "write ransomware" → INPUT RAIL keyword match in <50ms |
| `demo_2_encoded_attack.py` | Demo 2 — Encoded Attack | ~2 min | Base64/ROT13/leetspeak obfuscation → decode-then-classify pipeline |
| `demo_3_multi_turn_escalation.py` | Demo 3 — Multi-Turn Escalation | ~4 min | Innocent questions → DIALOG RAIL catches trajectory escalation |
| `demo_4_red_team_challenge.py` | Demo 4 — Red Team Challenge | ~3 min | 12 bypass techniques (synonyms, jailbreaks, encoding, framing) |

### Supporting Files

| File | Purpose |
|------|---------|
| `guardrail_engine.py` | Shared detection engine — keyword, decode, dialog, AST rails + terminal logging |
| `run_all_demos.py` | Master runner — executes all 4 demos in sequence |
| `config/config.yml` | NeMo Guardrails configuration (Azure OpenAI, 5 rail types) |
| `config/rails/security.co` | Colang security flows (intents, responses, flows) |
| `config/actions/check_ransomware_code.py` | Execution rail — AST-based code analyzer |

---

## Interactive Modes

Every demo supports `--interactive` for live audience participation:

```bash
# Demo 1: type your own prompts
python demo_1_direct_block.py --interactive

# Demo 2: paste your own encoded strings
python demo_2_encoded_attack.py --interactive

# Demo 3: have a multi-turn conversation (type 'reset' to clear)
python demo_3_multi_turn_escalation.py --interactive

# Demo 3 extended: run all 3 escalation scenarios
python demo_3_multi_turn_escalation.py --extended

# Demo 4: audience submits bypass attempts live
python demo_4_red_team_challenge.py --interactive

# Demo 4: generate JSON report for post-session analysis
python demo_4_red_team_challenge.py --report
```

---

## Using with NeMo Guardrails (Full Production Mode)

If NeMo Guardrails is installed, you can run the config directly:

```bash
pip install nemoguardrails

# Interactive chat with verbose rail logs
nemoguardrails chat --config ./config --verbose

# API server mode (for integration testing)
nemoguardrails server --config ./config --port 8000
```

The `config/` directory contains everything NeMo needs:
- `config.yml` — model config, rail pipeline, settings
- `rails/security.co` — Colang flows for ransomware detection
- `actions/check_ransomware_code.py` — execution rail action

---

## Architecture (Slide 7 Pipeline)

```
User Message
    │
    ▼
┌──────────────────────┐
│   INPUT RAILS        │ ◄── demo_1 (keywords), demo_2 (decode)
│   • Keyword match    │
│   • Decode + classify│
│   • Jailbreak check  │
└──────────┬───────────┘
           │ ALLOWED
           ▼
┌──────────────────────┐
│   DIALOG RAILS       │ ◄── demo_3 (trajectory analysis)
│   • Topic tracking   │
│   • Escalation check │
│   • Colang flows     │
└──────────┬───────────┘
           │ ALLOWED
           ▼
┌──────────────────────┐
│   LLM (GPT-4o)       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   EXECUTION RAILS    │ ◄── AST code analysis
│   • Parse to AST     │
│   • Dangerous combos │
│   • Block ransomware │
└──────────┬───────────┘
           │ ALLOWED
           ▼
┌──────────────────────┐
│   OUTPUT RAILS       │
│   • Content scan     │
│   • Payload check    │
└──────────┬───────────┘
           │ ALLOWED
           ▼
      Safe Response
```

---

## Fallback Plan (Network Issues)

If the live demo environment has network problems:

1. **Use these scripts** — they run entirely offline, no LLM needed
2. **Pre-record** — run `run_all_demos.py` and screen-capture the output
3. **Ollama fallback** — start Ollama locally and point config.yml to it:
   ```yaml
   models:
     - type: main
       engine: ollama
       model: llama3
   ```

---

## Detection Coverage

| Attack Type | Detection Layer | Confidence | Latency |
|-------------|----------------|------------|---------|
| Direct keywords | Input Rail | 99% | <10ms |
| Base64 encoding | Input Rail (decode) | 96% | ~15ms |
| ROT13 encoding | Input Rail (decode) | 94% | ~12ms |
| Leetspeak | Input Rail (decode) | 91% | ~10ms |
| Synonym replacement | Input Rail (combos) | 92% | ~8ms |
| Role-play jailbreak | Input Rail (keywords) | 99% | <10ms |
| Multi-turn escalation | Dialog Rail | 95% | ~5ms per turn |
| Code generation | Execution Rail (AST) | 98% | ~50ms |
| Dangerous combinations | Execution Rail (AST) | 95-99% | ~50ms |
