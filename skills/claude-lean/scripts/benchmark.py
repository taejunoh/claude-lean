#!/usr/bin/env python3
"""
Claude Lean — Benchmark Runner

Measures token counts and costs before and after optimization,
producing a verifiable comparison report.

Usage:
  python benchmark.py <claude_md_path> [--turns 10] [--output report.json]
  python benchmark.py --before <before.md> --after <after.md>
"""

import argparse
import json
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from count_tokens import count_tokens, count_tokens_in_file, find_claude_config_files
from analyze_cost import estimate_cost, MODELS
from optimize_claude_md import analyze


def run_benchmark(
    claude_md_path: str,
    turns: int = 10,
    cache_rate: float = 0.9,
    before_path: str = None,
    after_path: str = None,
) -> dict:
    """
    Run a full benchmark comparing before/after optimization.

    If before_path and after_path are given, compare those two files.
    Otherwise, analyze claude_md_path and simulate optimization.
    """
    # --- Before state ---
    if before_path:
        before_text = Path(before_path).read_text()
    else:
        before_text = Path(claude_md_path).read_text()

    before_tokens = count_tokens(before_text)
    before_bytes = len(before_text.encode("utf-8"))

    # --- After state ---
    if after_path:
        after_text = Path(after_path).read_text()
        after_tokens = count_tokens(after_text)
    else:
        # Simulate optimization by analyzing sections
        report = analyze(claude_md_path)
        after_tokens = report["total_tokens_after"]
        after_text = None  # We don't have actual optimized text in dry-run

    after_bytes = len(after_text.encode("utf-8")) if after_text else int(after_tokens * 4)

    # --- Context overhead (system prompt + MCP + skills) ---
    overhead_tokens = 20000  # system prompt baseline

    # --- Cost comparison ---
    before_total = before_tokens + overhead_tokens
    after_total = after_tokens + overhead_tokens
    token_diff = before_tokens - after_tokens

    before_costs = estimate_cost(before_total, turns=turns, cache_rate=cache_rate)
    after_costs = estimate_cost(after_total, turns=turns, cache_rate=cache_rate)

    cost_comparison = []
    for bc, ac in zip(before_costs, after_costs):
        cost_comparison.append({
            "model": bc.model_label,
            "before_no_cache": bc.cost_no_cache,
            "before_cached": bc.cost_with_cache,
            "after_no_cache": ac.cost_no_cache,
            "after_cached": ac.cost_with_cache,
            "savings_no_cache": round(bc.cost_no_cache - ac.cost_no_cache, 4),
            "savings_cached": round(bc.cost_with_cache - ac.cost_with_cache, 4),
            "savings_pct_no_cache": round(
                ((bc.cost_no_cache - ac.cost_no_cache) / max(bc.cost_no_cache, 0.0001)) * 100, 1
            ),
            "savings_pct_cached": round(
                ((bc.cost_with_cache - ac.cost_with_cache) / max(bc.cost_with_cache, 0.0001)) * 100, 1
            ),
        })

    # --- Accuracy verification ---
    naive_before = before_bytes // 4
    naive_after = after_bytes // 4
    naive_diff = naive_before - naive_after
    accuracy_comparison = {
        "tiktoken_before": before_tokens,
        "tiktoken_after": after_tokens,
        "tiktoken_reduction": token_diff,
        "naive_before": naive_before,
        "naive_after": naive_after,
        "naive_reduction": naive_diff,
        "naive_error_before_pct": round(
            ((naive_before - before_tokens) / max(before_tokens, 1)) * 100, 1
        ),
        "naive_error_after_pct": round(
            ((naive_after - after_tokens) / max(after_tokens, 1)) * 100, 1
        ),
    }

    return {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "turns": turns,
            "cache_rate": cache_rate,
            "overhead_tokens": overhead_tokens,
        },
        "before": {
            "tokens": before_tokens,
            "bytes": before_bytes,
            "total_per_turn": before_total,
        },
        "after": {
            "tokens": after_tokens,
            "bytes": after_bytes,
            "total_per_turn": after_total,
        },
        "reduction": {
            "tokens": token_diff,
            "pct": round((token_diff / max(before_tokens, 1)) * 100, 1),
        },
        "cost_comparison": cost_comparison,
        "accuracy_verification": accuracy_comparison,
    }


def format_benchmark(result: dict, fmt: str = "table") -> str:
    """Format benchmark results."""
    if fmt == "json":
        return json.dumps(result, indent=2)

    lines = []
    lines.append("=" * 80)
    lines.append("TOKEN DIET PRO — BENCHMARK REPORT")
    lines.append("=" * 80)
    lines.append(f"Timestamp: {result['timestamp']}")
    lines.append(f"Config: {result['config']['turns']} turns, "
                 f"{result['config']['cache_rate']:.0%} cache rate")
    lines.append("")

    # Token comparison
    lines.append("--- Token Comparison ---")
    b = result["before"]
    a = result["after"]
    r = result["reduction"]
    lines.append(f"  Before: {b['tokens']:>8,} tokens ({b['bytes']:,} bytes)")
    lines.append(f"  After:  {a['tokens']:>8,} tokens ({a.get('bytes', 0):,} bytes)")
    lines.append(f"  Saved:  {r['tokens']:>8,} tokens ({r['pct']}%)")
    lines.append("")

    # Accuracy verification
    av = result["accuracy_verification"]
    lines.append("--- Accuracy: tiktoken vs naive (bytes/4) ---")
    lines.append(f"  Before: tiktoken={av['tiktoken_before']:,} vs naive={av['naive_before']:,} "
                 f"(naive error: {av['naive_error_before_pct']:+.1f}%)")
    lines.append(f"  After:  tiktoken={av['tiktoken_after']:,} vs naive={av['naive_after']:,} "
                 f"(naive error: {av['naive_error_after_pct']:+.1f}%)")
    lines.append("")

    # Cost comparison
    lines.append("--- Cost Comparison (per session) ---")
    lines.append(f"{'Model':<28} {'Before':>10} {'After':>10} {'Saved':>10} {'%':>6}")
    lines.append("-" * 68)
    for c in result["cost_comparison"]:
        lines.append(
            f"{c['model']:<28} ${c['before_cached']:>8.4f} ${c['after_cached']:>8.4f} "
            f"${c['savings_cached']:>8.4f} {c['savings_pct_cached']:>5.0f}%"
        )
    lines.append("")
    lines.append("(Costs shown with cache; without cache savings are typically larger)")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Claude Lean — Benchmark Runner")
    parser.add_argument("file", nargs="?", help="CLAUDE.md file to benchmark")
    parser.add_argument("--before", help="Before-optimization file")
    parser.add_argument("--after", help="After-optimization file")
    parser.add_argument("--turns", type=int, default=10)
    parser.add_argument("--cache-rate", type=float, default=0.9)
    parser.add_argument("--format", choices=["table", "json"], default="table")
    parser.add_argument("--output", help="Save JSON results to file")

    args = parser.parse_args()

    if args.before and args.after:
        result = run_benchmark(
            args.before, turns=args.turns, cache_rate=args.cache_rate,
            before_path=args.before, after_path=args.after,
        )
    elif args.file:
        result = run_benchmark(args.file, turns=args.turns, cache_rate=args.cache_rate)
    else:
        print("Error: provide a CLAUDE.md file or --before/--after pair")
        sys.exit(1)

    print(format_benchmark(result, args.format))

    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2))
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
