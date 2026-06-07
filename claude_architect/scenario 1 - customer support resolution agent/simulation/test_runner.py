"""
Scenario 1 — Test Runner
========================
Runs all 12 test cases and measures First-Contact Resolution (FCR) rate.
Target: >= 80% FCR.

Usage:
    python test_runner.py              # Run all cases
    python test_runner.py --case C001  # Run specific case
    python test_runner.py --dry-run    # Show cases without calling API

Output:
    - Per-case PASS/FAIL with tool trace
    - FCR rate vs 80% target
    - Failure breakdown by complexity category
"""

import json
import os
import argparse
from agent import run_agent, DATASET


def run_all_cases(dry_run: bool = False, specific_case: str = None) -> dict:
    cases = DATASET["cases"]
    if specific_case:
        cases = [c for c in cases if c["id"] == specific_case]

    results = []
    passed = 0
    failed_cases = []

    print(f"\n{'='*70}")
    print(f"SCENARIO 1: CUSTOMER SUPPORT RESOLUTION AGENT")
    print(f"Target FCR: {DATASET['target_fcr']*100:.0f}%  |  Cases: {len(cases)}")
    print(f"{'='*70}")

    for case in cases:
        if dry_run:
            print(f"\n[DRY RUN] Case {case['id']}: {case['complexity'].upper()}")
            print(f"  Request: {case['request'][:80]}...")
            print(f"  Expected tools: {case['expected_tool_sequence']}")
            print(f"  Expected result: {case['expected_resolution']}")
            print(f"  Notes: {case['notes']}")
            continue

        result = run_agent(case, verbose=True)
        results.append(result)

        status = "PASS" if result["correct"] else "FAIL"
        print(f"\n  [{status}] Case {case['id']} ({case['complexity']})")

        if result["correct"]:
            passed += 1
        else:
            failed_cases.append({
                "case_id": case["id"],
                "complexity": case["complexity"],
                "expected": result["expected_resolution"],
                "actual": result["actual_resolution"],
                "tools_called": result["tools_called"],
                "notes": case["notes"]
            })

    if dry_run:
        return {}

    fcr_rate = passed / len(cases) if cases else 0
    target_met = fcr_rate >= DATASET["target_fcr"]

    print(f"\n{'='*70}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*70}")
    print(f"  Passed:  {passed}/{len(cases)}")
    print(f"  FCR Rate: {fcr_rate*100:.1f}%")
    print(f"  Target:  {DATASET['target_fcr']*100:.0f}%")
    print(f"  Status:  {'TARGET MET' if target_met else 'BELOW TARGET'}")

    if failed_cases:
        print(f"\nFAILED CASES ({len(failed_cases)}):")
        for fc in failed_cases:
            print(f"  - {fc['case_id']} [{fc['complexity']}]: expected={fc['expected']}, got={fc['actual']}")
            print(f"    Tools called: {fc['tools_called']}")
            print(f"    Notes: {fc['notes']}")

    # Breakdown by complexity
    complexity_counts = {}
    complexity_pass = {}
    for case in cases:
        c = case["complexity"]
        complexity_counts[c] = complexity_counts.get(c, 0) + 1
    for r in results:
        case = next(c for c in cases if c["id"] == r["case_id"])
        c = case["complexity"]
        if r["correct"]:
            complexity_pass[c] = complexity_pass.get(c, 0) + 1

    print(f"\nBREAKDOWN BY COMPLEXITY:")
    for c, total in complexity_counts.items():
        passed_c = complexity_pass.get(c, 0)
        rate = passed_c / total * 100
        bar = "█" * int(rate / 10) + "░" * (10 - int(rate / 10))
        print(f"  {c:<25} {bar} {rate:.0f}% ({passed_c}/{total})")

    return {
        "total": len(cases),
        "passed": passed,
        "fcr_rate": fcr_rate,
        "target_met": target_met,
        "failed_cases": failed_cases
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scenario 1 Test Runner")
    parser.add_argument("--dry-run", action="store_true", help="Show cases without calling API")
    parser.add_argument("--case", type=str, help="Run a specific case ID (e.g., C001)")
    args = parser.parse_args()

    run_all_cases(dry_run=args.dry_run, specific_case=args.case)
