"""
Why this file exists:
This is the actual answer to "how strict should the source guardrail be."
The system prompt ASKS the model to only cite real URLs. This file doesn't
trust that request - it checks it. Every URL the model claims in its final
brief gets compared against the set of URLs search_web genuinely returned
during this run. That comparison is the entire point: a prompt instruction
is a request the model might ignore or hallucinate around; this function
either finds the URL in the real evidence or it doesn't. Nothing in between,
nothing to interpret.
"""
from dataclasses import dataclass

MIN_REQUIRED_VERIFIED_SOURCES = 5


@dataclass
class VerificationResult:
    verified_sources: list[dict]      # sources whose URL was actually returned by search_web
    unverified_sources: list[dict]    # sources whose URL was NOT found - likely hallucinated
    passed: bool                      # True only if verified_sources meets the minimum


def verify_sources(claimed_sources: list[dict], seen_urls: set[str]) -> VerificationResult:
    """
    claimed_sources: the "sources" list from the model's submit_research_brief call.
    seen_urls: every URL returned by every search_web call this run.

    A source "passes" only on an exact URL match against something the tool
    actually returned. No fuzzy matching, no "close enough" - the whole
    value of this check is that it can't be talked into a false positive.
    """
    verified = []
    unverified = []

    for source in claimed_sources:
        url = source.get("url", "")
        if url in seen_urls:
            verified.append(source)
        else:
            unverified.append(source)

    return VerificationResult(
        verified_sources=verified,
        unverified_sources=unverified,
        passed=len(verified) >= MIN_REQUIRED_VERIFIED_SOURCES,
    )
