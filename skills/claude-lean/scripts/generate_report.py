#!/usr/bin/env python3
"""
Claude Lean — Report Generator

Produces a comprehensive markdown report combining:
  - Token scan results
  - Cost analysis
  - Optimization recommendations
  - Benchmark data (if available)

Usage:
  python generate_report.py [--output ~/.claude/claude-lean-report.md]
  python generate_report.py --benchmark-data benchmark.json --output report.md
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from count_tokens import find_claude_config_files, format_results, count_tokens
from analyze_cost import estimate_cost, format_cost_results


def generate_report(
    benchmark_data: dict = None,
    output_path: str = None,
) -> str:
    """Generate a comprehensive Claude Lean report."""
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append("# Claude Lean — Diagnostic Report")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append("")

    # --- Section 1: Token Scan ---
    lines.append("## 1. Per-Turn Token Consumption")
    lines.append("")

    config_results = find_claude_config_files()
    if config_results:
        total_config_tokens = sum(r["tokens"] for r in config_results)
        system_prompt_tokens = 20000
        total_per_turn = total_config_tokens + system_prompt_tokens

        lines.append("| Component | Tokens | Bytes | Grade | vs Naive |")
        lines.append("|-----------|--------|-------|-------|----------|")

        for r in config_results:
            tokens = r["tokens"]
            grade = _grade(tokens) if r.get("category") not in ("mcp_servers", "skills") else "—"
            delta = r.get("accuracy_delta_pct", 0)
            delta_str = f"{delta:+.1f}%" if delta != 0 else "—"
            lines.append(
                f"| {r.get('label', '?')} | {tokens:,} | {r.get('bytes', 0):,} | {grade} | {delta_str} |"
            )

        lines.append(f"| System prompt (est.) | {system_prompt_tokens:,} | — | — | — |")
        lines.append(f"| **TOTAL per turn** | **{total_per_turn:,}** | — | — | — |")
        lines.append("")

        # Naive estimation comparison
        total_naive = sum(r.get("naive_estimate", 0) for r in config_results)
        if total_naive > 0:
            error = ((total_config_tokens - total_naive) / total_naive) * 100
            lines.append(f"> **Measurement accuracy:** tiktoken counted {total_config_tokens:,} tokens vs "
                        f"naive estimate of {total_naive:,} ({error:+.1f}% difference).")
            lines.append("")
    else:
        total_per_turn = 20000
        lines.append("No Claude Code configuration files found.")
        lines.append("")

    # --- Section 2: Cost Estimates ---
    lines.append("## 2. Cost Estimates")
    lines.append("")

    for turns in [10, 50]:
        cost_results = estimate_cost(total_per_turn, turns=turns)
        lines.append(f"### {turns}-turn session")
        lines.append("")
        lines.append("| Model | No Cache | With Cache (90%) | Savings |")
        lines.append("|-------|----------|------------------|---------|")
        for r in cost_results:
            lines.append(
                f"| {r.model_label} | ${r.cost_no_cache:.4f} | "
                f"${r.cost_with_cache:.4f} | ${r.savings:.4f} ({r.savings_pct:.0f}%) |"
            )
        lines.append("")

    # --- Section 3: Optimization Analysis ---
    if config_results:
        lines.append("## 3. Optimization Opportunities")
        lines.append("")

        opportunities = []
        for r in config_results:
            if r.get("category") in ("global_claude_md", "project_claude_md"):
                if r["tokens"] > 2000:
                    opportunities.append(
                        f"- **{r['label']}** ({r['tokens']:,} tokens): RED zone. "
                        f"Run `python optimize_claude_md.py {r['path']} --report` for detailed analysis."
                    )
                elif r["tokens"] > 750:
                    opportunities.append(
                        f"- **{r['label']}** ({r['tokens']:,} tokens): YELLOW zone. "
                        f"Consider splitting large sections to refs/."
                    )
            elif r.get("category") == "mcp_servers":
                count = r.get("server_count", 0)
                if count > 3:
                    opportunities.append(
                        f"- **MCP Servers** ({count} active, ~{r['tokens']:,} tokens): "
                        f"Disable unused servers to save ~3,000 tokens each."
                    )
            elif r.get("category") == "memory":
                if r["tokens"] > 1000:
                    opportunities.append(
                        f"- **{r['label']}** ({r['tokens']:,} tokens): "
                        f"Consider trimming old entries."
                    )

        if opportunities:
            for opp in opportunities:
                lines.append(opp)
        else:
            lines.append("No immediate optimization opportunities found. Your config is lean!")
        lines.append("")

    # --- Section 4: Benchmark Data ---
    if benchmark_data:
        lines.append("## 4. Benchmark Results")
        lines.append("")
        b = benchmark_data
        lines.append(f"- **Before:** {b['before']['tokens']:,} tokens")
        lines.append(f"- **After:** {b['after']['tokens']:,} tokens")
        lines.append(f"- **Reduction:** {b['reduction']['tokens']:,} tokens ({b['reduction']['pct']}%)")
        lines.append("")

        lines.append("### Cost Impact")
        lines.append("")
        lines.append("| Model | Before | After | Saved | % |")
        lines.append("|-------|--------|-------|-------|---|")
        for c in b.get("cost_comparison", []):
            lines.append(
                f"| {c['model']} | ${c['before_cached']:.4f} | "
                f"${c['after_cached']:.4f} | ${c['savings_cached']:.4f} | "
                f"{c['savings_pct_cached']:.0f}% |"
            )
        lines.append("")

    # --- Section 5: Best Practices ---
    lines.append("## 5. Quick Tips")
    lines.append("")
    lines.append("1. **Keep CLAUDE.md under 3KB** — every turn re-reads it")
    lines.append("2. **Disable unused MCPs** — each adds ~3,000 tokens")
    lines.append("3. **Use Sonnet for simple tasks** — 5x cheaper than Opus")
    lines.append("4. **Maintain cache** — avoid model/MCP changes mid-session")
    lines.append("5. **Use `/clear` between tasks** — resets context accumulation")
    lines.append("6. **Set `CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-4-6`** — cheaper subagents")
    lines.append("")

    report = "\n".join(lines)

    if output_path:
        Path(output_path).write_text(report, encoding="utf-8")

    return report


def _grade(tokens: int) -> str:
    if tokens < 750:
        return "GREEN"
    elif tokens < 2000:
        return "YELLOW"
    else:
        return "RED"


def main():
    parser = argparse.ArgumentParser(description="Claude Lean — Report Generator")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--benchmark-data", help="Benchmark JSON to include")

    args = parser.parse_args()

    benchmark = None
    if args.benchmark_data:
        benchmark = json.loads(Path(args.benchmark_data).read_text())

    output_path = args.output or str(
        Path.home() / ".claude" / f"claude-lean-report-{datetime.now().strftime('%Y%m%d')}.md"
    )

    report = generate_report(benchmark_data=benchmark, output_path=output_path)
    print(report)
    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
