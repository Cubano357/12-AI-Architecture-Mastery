"""
Why this file exists:
A completion notification is a side effect of a run, not part of what the
run IS - the agent's job (research a question, produce a verified brief)
is fully done before this ever gets called. Keeping it in its own module,
called last from run.py and never from agent.py or verification.py, means
a Telegram outage can't break the actual research function - at worst,
run() logs a warning and the report still gets saved to disk either way.

Uses a direct HTTP call to Telegram's own Bot API - the same bot already
configured for this Claude Code session's Telegram channel, reused here
rather than asking for a second bot. No new dependency: requests is
already in requirements.txt for search_tool.py.
"""
import requests

from config import get_telegram_bot_token, get_telegram_chat_id
from verification import MIN_REQUIRED_VERIFIED_SOURCES, VerificationResult

TELEGRAM_API_BASE = "https://api.telegram.org"


def send_completion_summary(verification: VerificationResult, total_claimed: int) -> None:
    token = get_telegram_bot_token()
    chat_id = get_telegram_chat_id()

    if not token or not chat_id:
        print("(Telegram not configured - TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set - skipping notification.)")
        return

    status = "PASS" if verification.passed else "FAIL"
    text = (
        f"Research agent run complete: {status}\n"
        f"Cited: {total_claimed}\n"
        f"Verified: {len(verification.verified_sources)}\n"
        f"Minimum required: {MIN_REQUIRED_VERIFIED_SOURCES}\n"
        f"Result: {status}"
    )

    try:
        response = requests.post(
            f"{TELEGRAM_API_BASE}/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        # A failed notification is a warning, never a crash - the report
        # already exists on disk regardless of whether this message sends.
        print(f"(Telegram notification failed, continuing anyway: {exc})")
