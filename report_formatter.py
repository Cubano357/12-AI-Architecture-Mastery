"""
Why this file exists:
Separates "what the report says" from "how it's rendered." The agent loop
and verification logic produce plain Python data (dicts, a
VerificationResult); this file is the only place that knows what the
output file should look like. If you ever want to change the report to
HTML, JSON, or a different layout, this is the only file that changes.
"""
from verification import VerificationResult


def format_report(brief: dict, verification: VerificationResult) -> str:
    lines = []

    lines.append(f"# Research Brief: {brief['research_question']}")
    lines.append("")

    if not verification.passed:
        lines.append(
            f"> ⚠️ **VERIFICATION WARNING:** Only {len(verification.verified_sources)} of "
            f"{len(brief['sources'])} claimed sources could be confirmed as real search "
            "results. This report does not meet the minimum of "
            f"{3} verified sources and should not be treated as fully reliable. "
            "See 'Unverified Sources' below."
        )
        lines.append("")

    lines.append("## Executive Summary")
    lines.append(brief["executive_summary"])
    lines.append("")

    lines.append("## Key Findings")
    for item in brief["key_findings"]:
        lines.append(f"- {item['finding']} (source: {item['source_url']})")
    lines.append("")

    lines.append("## Opportunities")
    for item in brief["opportunities"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Risks")
    for item in brief["risks"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Sources")
    lines.append(f"**Verified ({len(verification.verified_sources)}):**")
    for source in verification.verified_sources:
        lines.append(f"- [{source['title']}]({source['url']})")

    if verification.unverified_sources:
        lines.append("")
        lines.append(
            f"**⚠️ Unverified ({len(verification.unverified_sources)}) - NOT found in "
            "actual search results, likely hallucinated, excluded from the count above:**"
        )
        for source in verification.unverified_sources:
            lines.append(f"- {source.get('title', '(no title)')} - {source.get('url', '(no url)')}")

    return "\n".join(lines)
