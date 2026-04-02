#!/usr/bin/env python3
"""
Claude Lean — CLAUDE.md Auto-Optimizer

Analyzes CLAUDE.md content and automatically classifies sections into:
  - ESSENTIAL: Rules/settings used every conversation → keep in CLAUDE.md
  - MOVABLE:   Task-specific guides → move to refs/ or .claude/rules/
  - REMOVABLE: Historical/verbose content → archive or delete

Can also apply optimizations automatically (with --apply).

Usage:
  python optimize_claude_md.py <claude_md_path> [--apply] [--backup]
  python optimize_claude_md.py <claude_md_path> --dry-run
  python optimize_claude_md.py <claude_md_path> --report
"""

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from count_tokens import count_tokens


# ---------------------------------------------------------------------------
# Section classification
# ---------------------------------------------------------------------------

@dataclass
class Section:
    heading: str
    level: int
    content: str
    tokens: int
    classification: str  # essential, movable, removable
    reason: str
    line_start: int
    line_end: int


# Patterns that indicate content should be moved out
MOVABLE_PATTERNS = [
    (r"```[\s\S]{200,}```", "Code block longer than 200 chars"),
    (r"(?:(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\s*){2,}", "UUID table"),
    (r"(?:https?://\S+\s*){5,}", "URL list (5+ URLs)"),
    (r"\|.*\|.*\|.*\n\|[-\s|]+\n(?:\|.*\|.*\|.*\n){5,}", "Large table (5+ rows)"),
    (r"(?:curl|wget|docker|kubectl|npm|pip)\s+\S+", "Deployment/CLI commands"),
    (r"(?:api|endpoint|route)\s*[:=]", "API endpoint definitions"),
]

REMOVABLE_PATTERNS = [
    (r"(?:incident|postmortem|outage)\s+(?:report|log|history)", "Incident/postmortem records"),
    (r"(?:changelog|history|log)\s*[:=\n]", "Changelog/history"),
    (r"(?:TODO|FIXME|HACK|XXX)\s*:", "TODO/FIXME comments"),
    (r"(?:deprecated|legacy|old)\s+", "Deprecated content markers"),
    (r"(?:meeting\s+notes?|standup|retro)", "Meeting notes"),
]

ESSENTIAL_PATTERNS = [
    (r"(?:always|never|must|required|important)\s+", "Strong directive"),
    (r"(?:coding\s+style|convention|standard)", "Coding standards"),
    (r"(?:do\s+not|don't|avoid|prefer)", "Behavioral rules"),
    (r"(?:format|structure|template)\s+(?:for|of)", "Output format rules"),
    (r"(?:when\s+(?:writing|creating|editing|reviewing))", "Action-specific rules"),
]


def _classify_section(heading: str, content: str, tokens: int) -> tuple[str, str]:
    """Classify a section as essential, movable, or removable."""
    full_text = f"{heading}\n{content}".lower()

    # Check removable patterns first
    for pattern, reason in REMOVABLE_PATTERNS:
        if re.search(pattern, full_text, re.IGNORECASE):
            return "removable", reason

    # Check movable patterns
    for pattern, reason in MOVABLE_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            return "movable", reason

    # Large sections without strong directives are likely movable
    if tokens > 500:
        has_essential = any(
            re.search(p, full_text, re.IGNORECASE) for p, _ in ESSENTIAL_PATTERNS
        )
        if not has_essential:
            return "movable", f"Large section ({tokens} tokens) without strong directives"

    # Check essential patterns
    for pattern, reason in ESSENTIAL_PATTERNS:
        if re.search(pattern, full_text, re.IGNORECASE):
            return "essential", reason

    # Default: if small enough, keep it
    if tokens < 200:
        return "essential", "Small section, safe to keep"

    return "movable", "No strong directives detected"


def parse_sections(text: str) -> list[Section]:
    """Parse markdown into sections by headings."""
    lines = text.split("\n")
    sections = []
    current_heading = "(preamble)"
    current_level = 0
    current_lines: list[str] = []
    current_start = 1

    for i, line in enumerate(lines, 1):
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            # Save previous section
            if current_lines or current_heading != "(preamble)":
                content = "\n".join(current_lines).strip()
                tokens = count_tokens(content)
                cls, reason = _classify_section(current_heading, content, tokens)
                sections.append(Section(
                    heading=current_heading,
                    level=current_level,
                    content=content,
                    tokens=tokens,
                    classification=cls,
                    reason=reason,
                    line_start=current_start,
                    line_end=i - 1,
                ))
            current_heading = heading_match.group(2)
            current_level = len(heading_match.group(1))
            current_lines = []
            current_start = i
        else:
            current_lines.append(line)

    # Last section
    content = "\n".join(current_lines).strip()
    if content or current_heading != "(preamble)":
        tokens = count_tokens(content)
        cls, reason = _classify_section(current_heading, content, tokens)
        sections.append(Section(
            heading=current_heading,
            level=current_level,
            content=content,
            tokens=tokens,
            classification=cls,
            reason=reason,
            line_start=current_start,
            line_end=len(lines),
        ))

    return sections


def analyze(filepath: str) -> dict:
    """Analyze a CLAUDE.md file and return optimization report."""
    path = Path(filepath)
    text = path.read_text(encoding="utf-8")
    total_tokens_before = count_tokens(text)
    sections = parse_sections(text)

    essential = [s for s in sections if s.classification == "essential"]
    movable = [s for s in sections if s.classification == "movable"]
    removable = [s for s in sections if s.classification == "removable"]

    essential_tokens = sum(s.tokens for s in essential)
    movable_tokens = sum(s.tokens for s in movable)
    removable_tokens = sum(s.tokens for s in removable)

    def _snippet(content: str, max_len: int = 200) -> str:
        """First N chars of content for LLM context review."""
        s = content.strip().replace("\n", " ")
        return s[:max_len] + "..." if len(s) > max_len else s

    def _section_detail(s: Section) -> dict:
        return {
            "heading": s.heading,
            "tokens": s.tokens,
            "reason": s.reason,
            "lines": f"{s.line_start}-{s.line_end}",
            "snippet": _snippet(s.content),
        }

    return {
        "file": str(path),
        "total_tokens_before": total_tokens_before,
        "total_tokens_after": essential_tokens,
        "reduction": total_tokens_before - essential_tokens,
        "reduction_pct": round(((total_tokens_before - essential_tokens) / max(total_tokens_before, 1)) * 100, 1),
        "sections": {
            "essential": [_section_detail(s) for s in essential],
            "movable": [_section_detail(s) for s in movable],
            "removable": [_section_detail(s) for s in removable],
        },
        "all_sections": [
            {
                "heading": s.heading,
                "tokens": s.tokens,
                "classification": s.classification,
                "reason": s.reason,
                "lines": f"{s.line_start}-{s.line_end}",
                "snippet": _snippet(s.content),
            }
            for s in sections
        ],
        "summary": {
            "essential_count": len(essential),
            "essential_tokens": essential_tokens,
            "movable_count": len(movable),
            "movable_tokens": movable_tokens,
            "removable_count": len(removable),
            "removable_tokens": removable_tokens,
        },
        "_sections_raw": sections,
    }


def apply_optimization(filepath: str, backup: bool = True) -> dict:
    """
    Apply optimizations: keep essential, move movable to refs/, remove removable.
    Returns report of what was done.
    """
    path = Path(filepath)
    report = analyze(filepath)
    sections = report.pop("_sections_raw")

    if backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_suffix(f".backup_{timestamp}.md")
        shutil.copy2(path, backup_path)
        report["backup"] = str(backup_path)

    # Create refs directory
    refs_dir = path.parent / "refs"
    refs_dir.mkdir(exist_ok=True)

    # Build optimized CLAUDE.md (essential only)
    essential_parts = []
    moved_files = []

    for section in sections:
        if section.classification == "essential":
            if section.heading != "(preamble)":
                essential_parts.append(f"{'#' * section.level} {section.heading}")
            essential_parts.append(section.content)
            essential_parts.append("")
        elif section.classification == "movable":
            # Move to refs/
            safe_name = re.sub(r"[^a-zA-Z0-9_-]", "-", section.heading.lower()).strip("-")
            ref_path = refs_dir / f"{safe_name}.md"
            ref_content = f"# {section.heading}\n\n{section.content}\n"
            ref_path.write_text(ref_content, encoding="utf-8")
            moved_files.append({"heading": section.heading, "moved_to": str(ref_path), "tokens": section.tokens})
            # Add reference pointer in CLAUDE.md
            essential_parts.append(f"<!-- Moved to refs/{safe_name}.md ({section.tokens} tokens saved) -->")
            essential_parts.append("")

    # Write optimized CLAUDE.md
    optimized_text = "\n".join(essential_parts).strip() + "\n"
    path.write_text(optimized_text, encoding="utf-8")

    report["moved_files"] = moved_files
    report["applied"] = True
    return report


def format_report(report: dict, fmt: str = "table") -> str:
    """Format analysis report."""
    report_copy = {k: v for k, v in report.items() if k != "_sections_raw"}

    if fmt == "json":
        return json.dumps(report_copy, indent=2, ensure_ascii=False)

    if fmt == "markdown":
        lines = [
            "## CLAUDE.md Optimization Report",
            "",
            f"**File:** `{report['file']}`",
            f"**Before:** {report['total_tokens_before']:,} tokens",
            f"**After:** {report['total_tokens_after']:,} tokens",
            f"**Reduction:** {report['reduction']:,} tokens ({report['reduction_pct']}%)",
            "",
        ]
        s = report["summary"]
        lines.append("### Section Breakdown")
        lines.append("")
        lines.append(f"- **Essential** ({s['essential_count']} sections, {s['essential_tokens']:,} tokens): Keep in CLAUDE.md")
        lines.append(f"- **Movable** ({s['movable_count']} sections, {s['movable_tokens']:,} tokens): Move to refs/")
        lines.append(f"- **Removable** ({s['removable_count']} sections, {s['removable_tokens']:,} tokens): Archive or delete")
        lines.append("")

        if report["sections"]["movable"]:
            lines.append("### Sections to Move")
            lines.append("")
            for sec in report["sections"]["movable"]:
                lines.append(f"- **{sec['heading']}** ({sec['tokens']} tokens) — {sec['reason']}")
            lines.append("")

        if report["sections"]["removable"]:
            lines.append("### Sections to Remove")
            lines.append("")
            for sec in report["sections"]["removable"]:
                lines.append(f"- ~~{sec['heading']}~~ ({sec['tokens']} tokens) — {sec['reason']}")

        return "\n".join(lines)

    # Default: table
    lines = []
    lines.append(f"CLAUDE.md Optimization Report: {report['file']}")
    lines.append(f"Before: {report['total_tokens_before']:,} tokens → After: {report['total_tokens_after']:,} tokens")
    lines.append(f"Reduction: {report['reduction']:,} tokens ({report['reduction_pct']}%)")
    lines.append("")

    for cls_name in ("essential", "movable", "removable"):
        cls_label = cls_name.upper()
        secs = report["sections"][cls_name]
        if secs:
            lines.append(f"  [{cls_label}]")
            for sec in secs:
                lines.append(f"    {sec['heading']:<40} {sec['tokens']:>6} tokens  — {sec['reason']}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Claude Lean — CLAUDE.md Optimizer")
    parser.add_argument("file", help="Path to CLAUDE.md")
    parser.add_argument("--apply", action="store_true", help="Apply optimizations (moves sections to refs/)")
    parser.add_argument("--backup", action="store_true", default=True, help="Create backup before applying")
    parser.add_argument("--no-backup", dest="backup", action="store_false")
    parser.add_argument("--dry-run", action="store_true", help="Analyze without applying (default)")
    parser.add_argument("--format", choices=["table", "json", "markdown"], default="table")
    parser.add_argument("--report", action="store_true", help="Generate detailed markdown report")

    args = parser.parse_args()

    if args.report:
        args.format = "markdown"

    if args.apply and not args.dry_run:
        report = apply_optimization(args.file, backup=args.backup)
    else:
        report = analyze(args.file)

    print(format_report(report, args.format))


if __name__ == "__main__":
    main()
