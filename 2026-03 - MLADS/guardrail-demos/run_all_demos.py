#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
  MLADS 2026 — Run All Demos
  Executes Demo 1 through Demo 4 in sequence.
  Use this for the pre-recorded fallback if the live demo fails.

  Run:
    python run_all_demos.py
═══════════════════════════════════════════════════════════════
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
from guardrail_engine import Color, print_header

def main():
    print(f"\n{Color.BOLD}{Color.CYAN}")
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║    MLADS 2026 — Defending Against LLM-Assisted         ║")
    print("  ║    Ransomware: Live Demo Suite                         ║")
    print("  ║                                                        ║")
    print("  ║    4 Demos  •  NeMo Guardrails  •  5-Layer Defense     ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print(f"{Color.RESET}\n")

    demos = [
        ("Demo 1 — Direct Block",          "demo_1_direct_block"),
        ("Demo 2 — Encoded Attack",         "demo_2_encoded_attack"),
        ("Demo 3 — Multi-Turn Escalation",  "demo_3_multi_turn_escalation"),
        ("Demo 4 — Red Team Challenge",     "demo_4_red_team_challenge"),
    ]

    overall_start = time.perf_counter()

    for i, (name, module_name) in enumerate(demos, 1):
        print(f"  {Color.CYAN}{'▬' * 60}{Color.RESET}")
        print(f"  {Color.BOLD}Starting {name} ({i}/4){Color.RESET}")
        print(f"  {Color.CYAN}{'▬' * 60}{Color.RESET}\n")

        module = __import__(module_name)
        module.run_scripted()

        if i < len(demos):
            print(f"\n  {Color.DIM}Press Enter to continue to next demo "
                  f"(or Ctrl+C to stop)...{Color.RESET}")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                print(f"\n  {Color.YELLOW}Demo suite stopped.{Color.RESET}\n")
                return

    total = time.perf_counter() - overall_start
    print(f"\n  {Color.CYAN}{'═' * 60}{Color.RESET}")
    print(f"  {Color.BOLD}{Color.GREEN}All 4 demos complete.{Color.RESET}  "
          f"Total time: {total:.1f}s")
    print(f"  {Color.CYAN}{'═' * 60}{Color.RESET}\n")

if __name__ == "__main__":
    main()
