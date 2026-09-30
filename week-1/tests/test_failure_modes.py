"""
Why this file exists:
The README's Evaluation section documented two failure paths as "needs
explicit negative test" rather than "pass" - this file is what turns that
into an actual, checkable claim. Two tests, matching the two gaps: does
verify_sources() actually catch a URL Tavily never returned, and does the
real run.py wiring actually exit with code 2 when too few sources verify.

No source file changes accompany this - agent.py, search_tool.py,
verification.py, and report_formatter.py are untouched. This proves the
CURRENT behavior; it does not add error handling that isn't there yet.
"""
import sys

import pytest

import run
from verification import MIN_REQUIRED_VERIFIED_SOURCES, verify_sources


def test_unreturned_url_is_flagged_unverified():
    """Test A: a cited URL that search_web never returned must be caught,
    not silently trusted."""
    seen_urls = {
        "https://real1.example.com",
        "https://real2.example.com",
        "https://real3.example.com",
        "https://real4.example.com",
        "https://real5.example.com",
    }
    claimed_sources = [
        {"title": "A real result", "url": "https://real1.example.com"},
        {"title": "Hallucinated - never returned by search_web", "url": "https://never-returned.example.com"},
    ]

    result = verify_sources(claimed_sources, seen_urls)

    assert result.verified_sources == [claimed_sources[0]]
    assert result.unverified_sources == [claimed_sources[1]]


def test_insufficient_verified_sources_exits_with_code_2(monkeypatch, tmp_path):
    """Test B: fewer than MIN_REQUIRED_VERIFIED_SOURCES verified sources
    must produce the system's actual documented failure state - exit code
    2 from run.py - not just a flag deep in verification.py.

    Only agent.run_agent is replaced (it's the network-calling boundary);
    everything downstream - verify_sources, format_report, the sys.exit(2)
    branch in run.main() - is the real, unmodified code."""
    seen_urls = {"https://real1.example.com", "https://real2.example.com"}
    fake_brief = {
        "research_question": "test question",
        "executive_summary": "test summary",
        "key_findings": [],
        "opportunities": [],
        "risks": [],
        # Only 2 of these are in seen_urls - below MIN_REQUIRED_VERIFIED_SOURCES (5).
        "sources": [
            {"title": "Real 1", "url": "https://real1.example.com"},
            {"title": "Real 2", "url": "https://real2.example.com"},
        ],
    }
    assert len(fake_brief["sources"]) < MIN_REQUIRED_VERIFIED_SOURCES

    monkeypatch.setattr(run, "run_agent", lambda question: (fake_brief, seen_urls))
    monkeypatch.setattr(sys, "argv", ["run.py", "test question"])
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        run.main()

    assert exc_info.value.code == 2
