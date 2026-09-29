"""
Why this file exists:
The single entry point. Its only job is: get the question from the user,
call the agent, verify the result, format it, and save/print it. It
deliberately contains no business logic of its own - every real decision
lives in the module responsible for it (agent.py decides how to research,
verification.py decides what counts as a real source, report_formatter.py
decides how it looks). This file just wires them together in order.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

from agent import run_agent
from verification import verify_sources
from report_formatter import format_report


def main():
    if len(sys.argv) < 2:
        print('Usage: python run.py "your research question"')
        sys.exit(1)

    research_question = sys.argv[1]

    print(f"Researching: {research_question}")
    print("(this calls the Claude API and a real web search - may take 10-30 seconds)")

    brief, seen_urls = run_agent(research_question)
    verification = verify_sources(brief["sources"], seen_urls)

    report_text = format_report(brief, verification)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_path = Path(f"report-{timestamp}.md")
    output_path.write_text(report_text, encoding="utf-8")

    print()
    print(report_text)
    print()
    print(f"Saved to {output_path}")

    if not verification.passed:
        # Non-zero exit on a failed verification, not just a warning in the
        # text - this is what makes "at least 3 verified sources" an
        # enforced success criterion rather than a suggestion, for anyone
        # (or any script) that checks this program's exit code.
        sys.exit(2)


if __name__ == "__main__":
    main()
