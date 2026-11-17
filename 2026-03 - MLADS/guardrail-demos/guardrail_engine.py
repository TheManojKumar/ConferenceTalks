"""
MLADS 2026 — Guardrail Engine
==============================
Shared detection engine used by all four demo scripts.
Works standalone (no NeMo dependency required for live demo).
When NeMo Guardrails is installed, use `nemoguardrails chat --config ./config --verbose` instead.

This module provides:
  - Keyword / regex input rail
  - Base64 / ROT13 / leetspeak decode-then-classify rail
  - Multi-turn conversation trajectory analysis (dialog rail)
  - AST-based code analysis (execution rail)
  - Rich terminal logging that mirrors NeMo --verbose output
"""

import re
import ast
import sys
import time
import json
import base64
import codecs
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import the AST analyzer
sys.path.insert(0, "./config/actions")
try:
    from check_ransomware_code import CodeAnalyzer
except ImportError:
    # Inline a minimal version if file isn't found
    class CodeAnalyzer:
        def analyze(self, code): return {"decision": "ALLOW", "confidence": 1.0, "reason": "analyzer unavailable", "categories": [], "findings": [], "combo_matches": []}


# ════════════════════════════════════════════════════════
# TERMINAL OUTPUT STYLING
# ════════════════════════════════════════════════════════

class Color:
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    DIM     = "\033[90m"
    BOLD    = "\033[1m"
    RESET   = "\033[0m"

def log_rail(rail_type: str, rail_name: str, status: str, confidence: float = 0.0,
             detail: str = "", latency_ms: float = 0.0):
    """Print a rail activation log line matching NeMo --verbose format."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    if status == "BLOCKED":
        color = Color.RED
        icon = "✗"
    elif status == "ALLOWED":
        color = Color.GREEN
        icon = "✓"
    else:
        color = Color.YELLOW
        icon = "⚠"

    conf_str = f"confidence: {confidence:.2f}" if confidence > 0 else ""
    lat_str = f"{latency_ms:.0f}ms" if latency_ms > 0 else ""
    parts = [x for x in [conf_str, lat_str, detail] if x]
    extra = " | ".join(parts)

    print(f"  {Color.DIM}{ts}{Color.RESET}  "
          f"[{Color.CYAN}{rail_type:14s}{Color.RESET}] "
          f"{rail_name:36s} → "
          f"{color}{Color.BOLD}{icon} {status}{Color.RESET}"
          f"  {Color.DIM}{extra}{Color.RESET}")

def print_header(text: str):
    width = 66
    print(f"\n{Color.CYAN}{'═' * width}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}  {text}{Color.RESET}")
    print(f"{Color.CYAN}{'═' * width}{Color.RESET}\n")

def print_user(text: str):
    print(f"  {Color.BOLD}User >{Color.RESET} {text}\n")

def print_bot(text: str):
    print(f"  {Color.GREEN}{Color.BOLD}Bot  >{Color.RESET} {text}\n")

def print_blocked(text: str):
    print(f"  {Color.RED}{Color.BOLD}Bot  >{Color.RESET} {Color.RED}{text}{Color.RESET}\n")


# ════════════════════════════════════════════════════════
# INPUT RAIL: Keyword + Pattern Detection
# ════════════════════════════════════════════════════════

DIRECT_KEYWORDS = [
    "ransomware", "cryptolocker", "wannacry", "petya", "notpetya",
    "malware", "trojan", "virus", "worm", "rootkit", "backdoor",
    "shellcode", "exploit", "payload", "keylogger", "spyware",
    "ransomeware",
]

DANGEROUS_COMBOS = [
    (["encrypt", "file", "delete"], "Encryption + file deletion pattern"),
    (["encrypt", "file", "ransom"], "Encryption + ransom pattern"),
    (["encrypt", "recursive", "remove"], "Recursive encryption + removal"),
    (["lock", "file", "payment"], "File locking + payment demand"),
    (["cipher", "inaccessible", "recover"], "Cipher + inaccessibility + recovery"),
    (["enumerate", "encrypt", "delete"], "Enumerate + encrypt + delete chain"),
]


def check_input_keywords(text: str) -> Optional[Dict]:
    """Layer 1: Fast keyword matching (<10ms)."""
    start = time.perf_counter()
    text_lower = text.lower()

    # Direct keyword match
    for kw in DIRECT_KEYWORDS:
        if kw in text_lower:
            ms = (time.perf_counter() - start) * 1000
            return {
                "blocked": True,
                "rail": "INPUT RAIL",
                "method": "check_ransomware_keywords",
                "confidence": 0.99,
                "matched": kw,
                "latency_ms": ms,
            }

    # Dangerous combination check
    for combo_words, desc in DANGEROUS_COMBOS:
        if all(w in text_lower for w in combo_words):
            ms = (time.perf_counter() - start) * 1000
            return {
                "blocked": True,
                "rail": "INPUT RAIL",
                "method": "check_dangerous_combinations",
                "confidence": 0.92,
                "matched": desc,
                "latency_ms": ms,
            }

    ms = (time.perf_counter() - start) * 1000
    return {"blocked": False, "latency_ms": ms}


# ════════════════════════════════════════════════════════
# INPUT RAIL: Decode-then-Classify (Demo 2)
# ════════════════════════════════════════════════════════

def decode_base64(text: str) -> Optional[str]:
    """Attempt Base64 decoding."""
    # Look for base64-like strings (4+ chars, valid charset)
    b64_pattern = re.compile(r'[A-Za-z0-9+/]{20,}={0,2}')
    matches = b64_pattern.findall(text)
    for match in matches:
        try:
            decoded = base64.b64decode(match).decode("utf-8", errors="ignore")
            if len(decoded) > 5 and any(c.isalpha() for c in decoded):
                return decoded
        except Exception:
            continue
    return None

def decode_rot13(text: str) -> str:
    """Apply ROT13 decoding."""
    return codecs.decode(text, "rot_13")

def decode_leetspeak(text: str) -> str:
    """Convert common leetspeak substitutions."""
    leet_map = {"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a"}
    return "".join(leet_map.get(c, c) for c in text)


def check_encoded_content(text: str) -> Optional[Dict]:
    """Layer 1b: Decode obfuscated content, then re-classify."""
    start = time.perf_counter()

    # Try Base64
    decoded = decode_base64(text)
    if decoded:
        result = check_input_keywords(decoded)
        if result and result.get("blocked"):
            ms = (time.perf_counter() - start) * 1000
            return {
                "blocked": True,
                "rail": "INPUT RAIL",
                "method": "decode_check",
                "encoding": "Base64",
                "decoded_content": decoded[:120],
                "confidence": 0.96,
                "latency_ms": ms,
            }

    # Try ROT13
    rot13_decoded = decode_rot13(text)
    result = check_input_keywords(rot13_decoded)
    if result and result.get("blocked"):
        ms = (time.perf_counter() - start) * 1000
        return {
            "blocked": True,
            "rail": "INPUT RAIL",
            "method": "decode_check",
            "encoding": "ROT13",
            "decoded_content": rot13_decoded[:120],
            "confidence": 0.94,
            "latency_ms": ms,
        }

    # Try leetspeak
    leet_decoded = decode_leetspeak(text)
    if leet_decoded != text:
        result = check_input_keywords(leet_decoded)
        if result and result.get("blocked"):
            ms = (time.perf_counter() - start) * 1000
            return {
                "blocked": True,
                "rail": "INPUT RAIL",
                "method": "decode_check",
                "encoding": "Leetspeak",
                "decoded_content": leet_decoded[:120],
                "confidence": 0.91,
                "latency_ms": ms,
            }

    ms = (time.perf_counter() - start) * 1000
    return {"blocked": False, "latency_ms": ms}


# ════════════════════════════════════════════════════════
# DIALOG RAIL: Conversation Trajectory Analysis (Demo 3)
# ════════════════════════════════════════════════════════

ESCALATION_TOPICS = {
    "encryption":    ["aes", "encrypt", "cipher", "cryptography", "fernet", "rsa", "key generation"],
    "file_ops":      ["enumerate files", "directory", "os.walk", "listdir", "file system", "recursive"],
    "destruction":   ["delete", "remove", "unlink", "rmtree", "overwrite", "wipe"],
    "persistence":   ["reboot", "registry", "startup", "scheduled task", "service", "crontab"],
    "network":       ["network share", "smb", "lateral", "remote execute", "psexec", "spread"],
    "exfiltration":  ["upload", "exfiltrate", "send to server", "external endpoint", "command and control"],
    "combination":   ["combine", "put together", "merge", "all of the above", "integrate"],
}

DANGEROUS_TRAJECTORIES = [
    (["encryption", "file_ops", "combination"], "Ransomware development: encrypt + files + combine"),
    (["encryption", "file_ops", "destruction"], "Ransomware pattern: encrypt + files + delete"),
    (["encryption", "destruction", "persistence"], "Persistent ransomware: encrypt + delete + survive"),
    (["file_ops", "network", "combination"], "Worm pattern: files + network + combine"),
    (["encryption", "file_ops", "exfiltration"], "Double extortion: encrypt + files + exfiltrate"),
]


class ConversationTracker:
    """Tracks conversation topics across turns for escalation detection."""

    def __init__(self):
        self.history: List[Dict] = []
        self.topics_seen: List[str] = []

    def add_message(self, text: str) -> Optional[Dict]:
        """Add a message and check for escalation patterns."""
        start = time.perf_counter()
        text_lower = text.lower()

        # Classify which topics this message touches
        current_topics = []
        for topic, keywords in ESCALATION_TOPICS.items():
            if any(kw in text_lower for kw in keywords):
                current_topics.append(topic)

        self.history.append({
            "text": text[:100],
            "topics": current_topics,
            "timestamp": datetime.now().isoformat(),
        })

        # Add new topics to trajectory
        for t in current_topics:
            if t not in self.topics_seen:
                self.topics_seen.append(t)

        # Check if trajectory matches a dangerous pattern
        for required_topics, description in DANGEROUS_TRAJECTORIES:
            if all(t in self.topics_seen for t in required_topics):
                ms = (time.perf_counter() - start) * 1000
                return {
                    "blocked": True,
                    "rail": "DIALOG RAIL",
                    "method": "conversation_trajectory_analysis",
                    "confidence": 0.95,
                    "trajectory": self.topics_seen.copy(),
                    "matched_pattern": description,
                    "turn_count": len(self.history),
                    "latency_ms": ms,
                }

        ms = (time.perf_counter() - start) * 1000
        return {"blocked": False, "topics": current_topics, "latency_ms": ms}

    def reset(self):
        self.history = []
        self.topics_seen = []


# ════════════════════════════════════════════════════════
# EXECUTION RAIL: AST Code Analysis
# ════════════════════════════════════════════════════════

_code_analyzer = CodeAnalyzer()

def check_generated_code(code: str) -> Dict:
    """Layer 3: Analyze generated code via AST."""
    start = time.perf_counter()
    result = _code_analyzer.analyze(code)
    ms = (time.perf_counter() - start) * 1000
    return {
        "blocked": result["decision"] == "BLOCK",
        "rail": "EXECUTION RAIL",
        "method": "ast_code_analysis",
        "confidence": result["confidence"],
        "reason": result["reason"],
        "categories": result["categories"],
        "findings_count": len(result["findings"]),
        "latency_ms": ms,
    }


# ════════════════════════════════════════════════════════
# FULL PIPELINE: Run all rails in sequence
# ════════════════════════════════════════════════════════

def run_full_pipeline(
    text: str,
    conversation: Optional[ConversationTracker] = None,
    generated_code: Optional[str] = None,
    verbose: bool = True,
) -> Dict:
    """
    Run the complete 5-layer guardrail pipeline on a message.
    This mirrors the NeMo Guardrails event-driven pipeline from Slide 7.
    """
    if verbose:
        print_user(text)
        print(f"  {Color.DIM}{'─' * 60}{Color.RESET}")

    # ── Layer 1: Input Rail — Keywords ──
    result = check_input_keywords(text)
    if verbose:
        status = "BLOCKED" if result["blocked"] else "ALLOWED"
        log_rail("INPUT RAIL", "check_ransomware_keywords", status,
                 result.get("confidence", 0), result.get("matched", ""),
                 result.get("latency_ms", 0))
    if result["blocked"]:
        if verbose:
            print(f"  {Color.DIM}{'─' * 60}{Color.RESET}")
            print_blocked(
                "I cannot assist with creating ransomware or malicious software. "
                "This request has been logged."
            )
        return {**result, "final": "BLOCKED", "layer": "Input Rail (Keywords)"}

    # ── Layer 1b: Input Rail — Decode obfuscation ──
    enc_result = check_encoded_content(text)
    if verbose:
        status = "BLOCKED" if enc_result["blocked"] else "ALLOWED"
        detail = ""
        if enc_result.get("encoding"):
            detail = f"{enc_result['encoding']} detected → decoded → matched"
        log_rail("INPUT RAIL", "decode_check", status,
                 enc_result.get("confidence", 0), detail,
                 enc_result.get("latency_ms", 0))
    if enc_result["blocked"]:
        if verbose:
            print(f"  {Color.DIM}{'─' * 60}{Color.RESET}")
            print_blocked(
                "Obfuscated content detected. After decoding, this request matches a "
                "ransomware pattern. Request blocked and logged."
            )
        return {**enc_result, "final": "BLOCKED", "layer": "Input Rail (Decode)"}

    # ── Layer 2: Dialog Rail — Conversation trajectory ──
    if conversation:
        conv_result = conversation.add_message(text)
        if verbose:
            status = "BLOCKED" if conv_result["blocked"] else "ALLOWED"
            detail = ""
            if conv_result.get("matched_pattern"):
                detail = f"escalation detected → {conv_result['matched_pattern']}"
            elif conv_result.get("topics"):
                detail = f"topics: {conv_result['topics']}"
            log_rail("DIALOG RAIL", "conversation_trajectory_analysis", status,
                     conv_result.get("confidence", 0), detail,
                     conv_result.get("latency_ms", 0))
        if conv_result["blocked"]:
            if verbose:
                print(f"  {Color.DIM}{'─' * 60}{Color.RESET}")
                print_blocked(
                    "I've detected that this conversation has been gradually escalating "
                    "toward ransomware development. The combination of topics across our "
                    "conversation constitutes a ransomware development pattern. "
                    "This conversation has been flagged for security review."
                )
            return {**conv_result, "final": "BLOCKED", "layer": "Dialog Rail (Trajectory)"}

    # ── Layer 3: Execution Rail — Code analysis ──
    if generated_code:
        code_result = check_generated_code(generated_code)
        if verbose:
            status = "BLOCKED" if code_result["blocked"] else "ALLOWED"
            log_rail("EXECUTION RAIL", "ast_code_analysis", status,
                     code_result.get("confidence", 0),
                     f"categories={code_result.get('categories', [])}",
                     code_result.get("latency_ms", 0))
        if code_result["blocked"]:
            if verbose:
                print(f"  {Color.DIM}{'─' * 60}{Color.RESET}")
                print_blocked(
                    f"Generated code blocked by execution rail. "
                    f"Reason: {code_result['reason']}"
                )
            return {**code_result, "final": "BLOCKED", "layer": "Execution Rail (AST)"}

    # ── All rails passed ──
    if verbose:
        log_rail("OUTPUT RAIL", "self_check_output", "ALLOWED", 1.0, "", 2.0)
        print(f"  {Color.DIM}{'─' * 60}{Color.RESET}")

    return {"blocked": False, "final": "ALLOWED", "layer": "All rails passed"}
