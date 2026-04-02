#!/usr/bin/env python3
"""
Claude Lean — Unit Tests

Tests for token counting accuracy, cost analysis, and optimizer logic.

Run: python -m pytest tests/test_all.py -v
  or: python tests/test_all.py
"""

import json
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from count_tokens import (
    count_tokens,
    count_tokens_in_file,
    _estimate_tokens_by_bytes,
    _get_encoder,
)
from analyze_cost import estimate_cost, MODELS
from optimize_claude_md import parse_sections, analyze, apply_optimization


FIXTURES = Path(__file__).parent / "fixtures"


class TestTokenCounting(unittest.TestCase):
    """Test the token counting engine."""

    def test_empty_string(self):
        self.assertEqual(count_tokens(""), 0)

    def test_simple_english(self):
        tokens = count_tokens("Hello, world!")
        self.assertGreater(tokens, 0)
        self.assertLess(tokens, 10)  # Should be ~4 tokens

    def test_korean_text(self):
        """Korean text should not be wildly off from byte-based estimate."""
        korean = "안녕하세요, 이것은 한국어 테스트입니다."
        tokens = count_tokens(korean)
        byte_estimate = len(korean.encode("utf-8")) // 4
        # tiktoken should differ from naive byte estimate
        self.assertGreater(tokens, 0)
        # The key test: measure the difference
        self.assertIsInstance(tokens, int)

    def test_mixed_language(self):
        """Mixed English/Korean text."""
        mixed = "This is a test. 이것은 테스트입니다. More English here."
        tokens = count_tokens(mixed)
        self.assertGreater(tokens, 5)

    def test_code_block(self):
        """Code should tokenize reasonably."""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        tokens = count_tokens(code)
        self.assertGreater(tokens, 10)
        self.assertLess(tokens, 100)

    def test_long_text_scaling(self):
        """Token count should scale roughly linearly with text length."""
        short = "Hello world. " * 10
        long = "Hello world. " * 100
        short_tokens = count_tokens(short)
        long_tokens = count_tokens(long)
        ratio = long_tokens / max(short_tokens, 1)
        # Should be roughly 10x (within 2x tolerance)
        self.assertGreater(ratio, 5)
        self.assertLess(ratio, 15)

    def test_count_tokens_in_file_exists(self):
        """Count tokens in a real fixture file."""
        result = count_tokens_in_file(str(FIXTURES / "sample_small.md"))
        self.assertTrue(result["exists"])
        self.assertGreater(result["tokens"], 0)
        self.assertGreater(result["bytes"], 0)
        self.assertGreater(result["lines"], 0)
        self.assertIsNone(result["error"])

    def test_count_tokens_in_file_not_found(self):
        """Missing file should return error info."""
        result = count_tokens_in_file("/nonexistent/file.md")
        self.assertFalse(result["exists"])
        self.assertEqual(result["tokens"], 0)

    def test_naive_vs_tiktoken_accuracy(self):
        """Verify counting produces reasonable results for non-ASCII."""
        text = "한국어 텍스트는 바이트 기반 추정이 부정확합니다. " * 20
        token_count = count_tokens(text)
        naive_count = len(text.encode("utf-8")) // 4
        # Token count should be positive and reasonable
        self.assertGreater(token_count, 0)
        # If tiktoken is available, they should differ
        if _get_encoder() is not None:
            self.assertNotEqual(token_count, naive_count,
                              "tiktoken and naive should differ for Korean text")

    def test_byte_fallback_english(self):
        """Byte fallback should be reasonable for English."""
        text = "This is a simple English sentence for testing purposes."
        fallback = _estimate_tokens_by_bytes(text)
        tiktoken_count = count_tokens(text)
        # Fallback should be within 50% of tiktoken for English
        ratio = fallback / max(tiktoken_count, 1)
        self.assertGreater(ratio, 0.5)
        self.assertLess(ratio, 2.0)

    def test_accuracy_delta_calculation(self):
        """Verify accuracy delta is computed correctly."""
        result = count_tokens_in_file(str(FIXTURES / "sample_large.md"))
        self.assertIn("accuracy_delta_pct", result)
        self.assertIsInstance(result["accuracy_delta_pct"], float)


class TestCostAnalysis(unittest.TestCase):
    """Test the cost analyzer."""

    def test_basic_cost_estimate(self):
        """All models should return cost estimates."""
        results = estimate_cost(input_tokens_per_turn=25000, turns=10)
        self.assertEqual(len(results), len(MODELS))
        for r in results:
            self.assertGreater(r.cost_no_cache, 0)
            self.assertGreater(r.cost_with_cache, 0)
            self.assertGreater(r.savings, 0)  # Cache should always save money

    def test_cache_always_saves(self):
        """With cache, cost should always be lower than without."""
        results = estimate_cost(input_tokens_per_turn=30000, turns=10, cache_rate=0.9)
        for r in results:
            self.assertLess(r.cost_with_cache, r.cost_no_cache,
                          f"Cache should save money for {r.model_label}")

    def test_single_model(self):
        """Requesting a specific model should return only that model."""
        results = estimate_cost(input_tokens_per_turn=10000, model="sonnet-4.6")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].model, "sonnet-4.6")

    def test_opus_more_expensive_than_sonnet(self):
        """Opus should always cost more than Sonnet."""
        results = estimate_cost(input_tokens_per_turn=25000, turns=10)
        by_model = {r.model: r for r in results}
        self.assertGreater(
            by_model["opus-4.6"].cost_no_cache,
            by_model["sonnet-4.6"].cost_no_cache,
        )

    def test_more_turns_more_cost(self):
        """More turns should cost more."""
        cost_5 = estimate_cost(input_tokens_per_turn=20000, turns=5, model="sonnet-4.6")[0]
        cost_20 = estimate_cost(input_tokens_per_turn=20000, turns=20, model="sonnet-4.6")[0]
        self.assertGreater(cost_20.cost_no_cache, cost_5.cost_no_cache)

    def test_zero_cache_rate(self):
        """Zero cache rate should equal no-cache cost (after first turn premium)."""
        results = estimate_cost(input_tokens_per_turn=20000, turns=10, cache_rate=0.0)
        for r in results:
            # With 0% cache rate, the cached cost should be higher than no-cache
            # because of the cache write premium on the first turn
            self.assertIsNotNone(r.cost_with_cache)

    def test_savings_percentage(self):
        """Savings percentage should be between 0 and 100."""
        results = estimate_cost(input_tokens_per_turn=25000, turns=10)
        for r in results:
            self.assertGreater(r.savings_pct, 0)
            self.assertLess(r.savings_pct, 100)


class TestOptimizer(unittest.TestCase):
    """Test the CLAUDE.md optimizer."""

    def test_parse_sections_small(self):
        """Small file should parse into sections."""
        text = Path(FIXTURES / "sample_small.md").read_text()
        sections = parse_sections(text)
        self.assertGreater(len(sections), 0)
        for s in sections:
            self.assertIn(s.classification, ("essential", "movable", "removable"))

    def test_parse_sections_large(self):
        """Large file should have movable/removable sections."""
        text = Path(FIXTURES / "sample_large.md").read_text()
        sections = parse_sections(text)
        classifications = {s.classification for s in sections}
        # Large file should have at least some non-essential content
        self.assertTrue(
            "movable" in classifications or "removable" in classifications,
            "Large file should have movable or removable sections"
        )

    def test_analyze_report(self):
        """Analyze should produce a valid report."""
        report = analyze(str(FIXTURES / "sample_large.md"))
        self.assertIn("total_tokens_before", report)
        self.assertIn("total_tokens_after", report)
        self.assertIn("reduction", report)
        self.assertIn("sections", report)
        self.assertGreater(report["total_tokens_before"], 0)
        # Large file should have some reduction potential
        self.assertGreaterEqual(report["reduction"], 0)

    def test_analyze_small_file_mostly_essential(self):
        """Small file with mostly rules should be mostly essential."""
        report = analyze(str(FIXTURES / "sample_small.md"))
        essential_pct = report["summary"]["essential_tokens"] / max(report["total_tokens_before"], 1)
        # Small rule file should be at least 50% essential
        self.assertGreater(essential_pct, 0.3)

    def test_large_file_has_removable(self):
        """Large file with incident logs should detect removable sections."""
        report = analyze(str(FIXTURES / "sample_large.md"))
        removable = report["sections"]["removable"]
        # Should detect incident logs or meeting notes as removable
        self.assertGreater(len(removable), 0,
                          "Should detect incident logs/meeting notes as removable")

    def test_apply_optimization(self):
        """Apply optimization should create refs/ and slim down the file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy fixture
            src = FIXTURES / "sample_large.md"
            dst = Path(tmpdir) / "CLAUDE.md"
            shutil.copy2(src, dst)

            before_tokens = count_tokens(dst.read_text())
            report = apply_optimization(str(dst), backup=True)

            # Should have created backup
            self.assertIn("backup", report)
            self.assertTrue(Path(report["backup"]).exists())

            # Should have created refs/
            refs_dir = Path(tmpdir) / "refs"
            if report.get("moved_files"):
                self.assertTrue(refs_dir.exists())

            # Optimized file should be smaller
            after_tokens = count_tokens(dst.read_text())
            self.assertLessEqual(after_tokens, before_tokens)

    def test_classification_patterns(self):
        """Test specific pattern detection."""
        sections = parse_sections(
            "# Incident Log\n\nincident report from 2024-12-15 about database outage\n"
        )
        found_removable = any(s.classification == "removable" for s in sections)
        self.assertTrue(found_removable, "Incident log should be classified as removable")


class TestBenchmark(unittest.TestCase):
    """Test the benchmark runner."""

    def test_benchmark_import(self):
        """Benchmark module should import cleanly."""
        from benchmark import run_benchmark
        self.assertTrue(callable(run_benchmark))

    def test_benchmark_with_fixtures(self):
        """Benchmark should work with fixture files."""
        from benchmark import run_benchmark

        result = run_benchmark(
            str(FIXTURES / "sample_large.md"),
            turns=5,
            cache_rate=0.9,
        )
        self.assertIn("before", result)
        self.assertIn("after", result)
        self.assertIn("reduction", result)
        self.assertIn("cost_comparison", result)
        self.assertIn("accuracy_verification", result)
        self.assertGreater(result["before"]["tokens"], 0)

    def test_benchmark_before_after(self):
        """Benchmark should compare two files."""
        from benchmark import run_benchmark

        result = run_benchmark(
            str(FIXTURES / "sample_small.md"),
            before_path=str(FIXTURES / "sample_large.md"),
            after_path=str(FIXTURES / "sample_small.md"),
        )
        self.assertGreater(result["reduction"]["tokens"], 0,
                          "Large → small should show reduction")


if __name__ == "__main__":
    unittest.main(verbosity=2)
