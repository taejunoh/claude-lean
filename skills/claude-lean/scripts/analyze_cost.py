#!/usr/bin/env python3
"""
Claude Lean — Cost Analyzer

Calculates per-turn and per-session costs across Claude models,
with cache hit/miss scenarios.

Usage:
  python analyze_cost.py --tokens 25000 [--turns 10] [--cache-rate 0.9]
  python analyze_cost.py --scan [--turns 10] [--cache-rate 0.9]
  python analyze_cost.py --format json|table|markdown
"""

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Model pricing (per 1M tokens, as of 2025-Q4)
# ---------------------------------------------------------------------------

MODELS = {
    "haiku-4.5": {
        "label": "Claude Haiku 4.5",
        "input": 1.00,
        "output": 5.00,
        "cache_read": 0.10,
        "cache_write": 1.25,
    },
    "sonnet-4.6": {
        "label": "Claude Sonnet 4.6",
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
        "cache_write": 3.75,
    },
    "opus-4.6": {
        "label": "Claude Opus 4.6",
        "input": 15.00,
        "output": 75.00,
        "cache_read": 1.50,
        "cache_write": 18.75,
    },
    "opus-4.6-fast": {
        "label": "Claude Opus 4.6 (Fast)",
        "input": 30.00,
        "output": 150.00,
        "cache_read": 3.00,
        "cache_write": 37.50,
    },
}


@dataclass
class CostEstimate:
    model: str
    model_label: str
    input_tokens: int
    output_tokens: int
    turns: int
    cache_rate: float
    cost_no_cache: float
    cost_with_cache: float
    savings: float
    savings_pct: float


def estimate_cost(
    input_tokens_per_turn: int,
    output_tokens_per_turn: int = 1000,
    turns: int = 10,
    cache_rate: float = 0.9,
    model: Optional[str] = None,
) -> list[CostEstimate]:
    """
    Estimate session cost across models.

    Args:
        input_tokens_per_turn: Total input tokens per turn (system + context)
        output_tokens_per_turn: Average output tokens per turn
        turns: Number of turns in the session
        cache_rate: Fraction of input tokens that hit cache (0.0 - 1.0)
        model: Specific model to estimate (None = all models)
    """
    results = []
    models_to_check = {model: MODELS[model]} if model and model in MODELS else MODELS

    for model_key, pricing in models_to_check.items():
        # No-cache scenario
        input_cost_no_cache = (input_tokens_per_turn * turns / 1_000_000) * pricing["input"]
        output_cost = (output_tokens_per_turn * turns / 1_000_000) * pricing["output"]
        total_no_cache = input_cost_no_cache + output_cost

        # With-cache scenario
        cached_tokens = int(input_tokens_per_turn * cache_rate)
        uncached_tokens = input_tokens_per_turn - cached_tokens

        # First turn: all tokens are cache-write; subsequent turns: cached portion reads from cache
        first_turn_cost = (
            (input_tokens_per_turn / 1_000_000) * pricing["cache_write"]
            + (output_tokens_per_turn / 1_000_000) * pricing["output"]
        )
        subsequent_turn_cost = (
            (cached_tokens / 1_000_000) * pricing["cache_read"]
            + (uncached_tokens / 1_000_000) * pricing["input"]
            + (output_tokens_per_turn / 1_000_000) * pricing["output"]
        )
        total_with_cache = first_turn_cost + subsequent_turn_cost * (turns - 1)

        savings = total_no_cache - total_with_cache
        savings_pct = (savings / max(total_no_cache, 0.0001)) * 100

        results.append(CostEstimate(
            model=model_key,
            model_label=pricing["label"],
            input_tokens=input_tokens_per_turn,
            output_tokens=output_tokens_per_turn,
            turns=turns,
            cache_rate=cache_rate,
            cost_no_cache=round(total_no_cache, 4),
            cost_with_cache=round(total_with_cache, 4),
            savings=round(savings, 4),
            savings_pct=round(savings_pct, 1),
        ))

    return results


def format_cost_results(results: list[CostEstimate], fmt: str = "table") -> str:
    """Format cost estimates."""
    if fmt == "json":
        return json.dumps([r.__dict__ for r in results], indent=2)

    if fmt == "markdown":
        lines = [
            f"## Cost Estimate ({results[0].turns}-turn session, {results[0].cache_rate:.0%} cache rate)",
            "",
            "| Model | No Cache | With Cache | Savings |",
            "|-------|----------|------------|---------|",
        ]
        for r in results:
            lines.append(
                f"| {r.model_label} | ${r.cost_no_cache:.4f} | "
                f"${r.cost_with_cache:.4f} | ${r.savings:.4f} ({r.savings_pct:.0f}%) |"
            )
        return "\n".join(lines)

    # Default: table
    lines = []
    r0 = results[0]
    lines.append(f"Session: {r0.turns} turns, {r0.input_tokens:,} input tokens/turn, "
                 f"{r0.output_tokens:,} output tokens/turn, {r0.cache_rate:.0%} cache rate")
    lines.append("")
    lines.append(f"{'Model':<28} {'No Cache':>12} {'Cached':>12} {'Savings':>12} {'Savings%':>10}")
    lines.append("-" * 78)
    for r in results:
        lines.append(
            f"{r.model_label:<28} ${r.cost_no_cache:>10.4f} ${r.cost_with_cache:>10.4f} "
            f"${r.savings:>10.4f} {r.savings_pct:>8.0f}%"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Claude Lean — Cost Analyzer")
    parser.add_argument("--tokens", type=int, help="Input tokens per turn")
    parser.add_argument("--output-tokens", type=int, default=1000, help="Output tokens per turn")
    parser.add_argument("--turns", type=int, default=10, help="Number of turns")
    parser.add_argument("--cache-rate", type=float, default=0.9, help="Cache hit rate (0-1)")
    parser.add_argument("--model", choices=list(MODELS.keys()), help="Specific model")
    parser.add_argument("--format", choices=["table", "json", "markdown"], default="table")
    parser.add_argument("--scan", action="store_true", help="Auto-detect tokens from Claude config")

    args = parser.parse_args()

    if args.scan:
        try:
            from count_tokens import find_claude_config_files
        except ImportError:
            sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
            from count_tokens import find_claude_config_files

        config_results = find_claude_config_files()
        total = sum(r["tokens"] for r in config_results) + 20000  # + system prompt
        args.tokens = total

    if not args.tokens:
        print("Error: --tokens required (or use --scan to auto-detect)")
        sys.exit(1)

    results = estimate_cost(
        input_tokens_per_turn=args.tokens,
        output_tokens_per_turn=args.output_tokens,
        turns=args.turns,
        cache_rate=args.cache_rate,
        model=args.model,
    )
    print(format_cost_results(results, args.format))


if __name__ == "__main__":
    main()
