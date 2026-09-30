# Week 1 — Business Research Agent

**Program:** 12-Week AI Solutions Architect Mastery
**Role split:** David El Corderu Bey, PhD = Solutions Architect / project owner. Claude = Senior AI Engineer / pair programmer, implementing and teaching the architecture, not deciding it unilaterally.

## What this is

A single Claude agent with two tools:
1. `search_web` (Tavily) — the agent's only way to gather real, current evidence.
2. `submit_research_brief` — a structured "final answer" tool. Forcing the output through a schema instead of free text is what makes source verification a plain data check instead of parsing prose.

The agent researches a business question about a small medical practice (chiropractic offices as the v1 use case) and returns a structured brief: Research Question, Executive Summary, Key Findings, Opportunities, Risks, Sources.

## Architecture

Mapped directly from the implementation — every box below corresponds to a real file and function, not an aspirational design.

![Business Research Agent architecture diagram](./architecture-diagram.svg)

## The one non-negotiable architectural decision

**Every cited source is verified against real tool output before the report is trusted.** `verification.py` compares each URL in the model's submitted `sources` list against the actual set of URLs `search_web` returned during that run. Anything that doesn't match is flagged as unverified and excluded from the "verified" count. If fewer than 5 sources verify, the report ships with a loud warning and the program exits non-zero — this was tightened from "ask the model nicely" to "check it in code" specifically because a prompt instruction is a request the model can get wrong; a set-membership check cannot.

## Hard scope boundary

The system prompt (`system_prompt.py`) draws a hard line: business research only (competitors, reputation, market trends), never clinical advice about a patient. This is a prompt-level rule only in v1 — there's no code-level check that a question or answer stayed in scope. That's an open item, not an oversight (see below).

## Files and why each exists

| File | Responsibility |
|---|---|
| `config.py` | The only place that knows where API keys come from. |
| `search_tool.py` | The only file that knows Tavily exists — schema + real HTTP call. |
| `report_tool.py` | The structured "final answer" schema that turns free text into checkable data. |
| `system_prompt.py` | The agent's rules: scope boundary + "only cite real URLs." |
| `agent.py` | The actual agent loop: call Claude, execute any tool it requests, feed results back, stop when it submits a brief. |
| `verification.py` | The deterministic source check — the piece this session's approval process specifically tightened. |
| `report_formatter.py` | Turns the brief + verification result into the final markdown, honestly, including flagging anything unverified. |
| `run.py` | Entry point — wires the above together, contains no decisions of its own. |

## Explicitly NOT built (and why)

- **No database.** Nothing needs to persist across runs yet — each question produces one file.
- **No RAG / vector store.** This researches the live web per question; there's no fixed private corpus to index.
- **No multi-agent orchestration.** One agent making its own tool-use decisions covers every success criterion in the approved scope. Adding a planner/critic/writer split here would be complexity sold to a problem that didn't ask for it.
- **No framework (LangChain, etc.).** Direct API calls keep the actual mechanics visible — that visibility is the point of Week 1.

## Status

**Live validation**

| Check | Result |
|---|---|
| Claude API | Passed |
| Tavily API | Passed |
| Minimum verified sources required | 5 |
| Latest test | 14 cited / 14 verified |
| Exit code | 0 |
| Test question | "What local marketing tactics work best for a new chiropractic office trying to attract its first patients?" |
| Date (UTC) | 2026-09-30 |

Full, unedited output of this run is committed as [`SAMPLE_VERIFIED_RUN.md`](./SAMPLE_VERIFIED_RUN.md) — this is evidence that it worked, not a claim that it should. See `CASE_STUDY.md` for the narrative.

Needs `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` in a `.env` file (see `.env.example`) or as environment variables.

## Evaluation

What's actually been tested versus what's still open — a scope statement, not a passing grade.

| Test | Result |
|---|---|
| Valid research question produces a brief | Pass |
| ≥5 verified sources on a real run | Pass |
| 14/14 source membership verification (cited URL was actually returned by search_web) | Pass |
| Invalid / unreturned URL correctly flagged as unverified | Needs explicit negative test |
| Insufficient verified sources correctly fails with exit code 2 | Needs explicit negative test |
| Clinical-question boundary enforcement | Not code-enforced (prompt-only, see above) |
| Claim/source semantic alignment — does the cited page actually support the claim, not just exist | Not evaluated |

**Source verification ≠ claim verification.** `verify_sources()` proves a cited URL is one `search_web` genuinely returned this run — it does not prove that URL's content actually supports the specific finding attached to it. That second check would require reading the source content and judging semantic support, which is a real (and harder) evaluation problem, not a set-membership check. This is a documented limitation of v1, not a flaw discovered after the fact.

## Security notes

Known risk surface for a Week 1 MVP, documented from actually reading the code — not all of it is mitigated yet. The goal here is demonstrating the risks are identified, not claiming they're closed.

**API keys / secrets**
- `ANTHROPIC_API_KEY`, `TAVILY_API_KEY` (required) and `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (optional) all enter the system as environment variables, read in `config.py` via `os.environ.get()` — never hardcoded, never committed (`.env` is gitignored).
- `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` are never printed or logged anywhere in this codebase.
- `TELEGRAM_BOT_TOKEN` **is a real gap**: `notify.py` builds the request URL as `.../bot{token}/sendMessage`, and if that request fails, the exception is caught and printed with `print(f"...{exc}")` — `requests` exceptions commonly include the failed URL in their string form, which would leak the token to stdout/logs on a failed send. Not fixed in v1. (This path is currently dormant — `run.py` doesn't call `notify.py` yet — but the risk is real the moment it's wired in.)

**What's sent to Claude:** the user's research question, the system prompt, and the full content of every `search_web` result (title, URL, and a text snippet from Tavily) — that snippet is third-party web content, verbatim.

**What's sent to Tavily:** only the search query strings the model generates, plus the Tavily API key for auth. No user-identifying data.

**Prompt-injection risk from web content — real, unmitigated:** `search_tool.py` returns raw, unsanitized snippets scraped from third-party pages, and `agent.py` feeds that content straight back into Claude's conversation as `tool_result` content with no filtering or injection defense. A compromised or malicious page could embed text designed to look like an instruction. Nothing in this codebase currently detects that.

**Is retrieved web content treated as untrusted input? Not explicitly.** There's no delimiter, framing, or instruction in `system_prompt.py` telling the model to treat `search_web` results with more suspicion than any other input. The only real control in the system is `verification.py`'s after-the-fact URL-membership check — which catches a citation for a URL that was never returned, but would **not** catch an injected instruction hidden inside the content of a URL that *was* genuinely returned.

## Open items for Phase 2 (not this week)

- Code-level enforcement of the non-clinical scope boundary (currently prompt-only).
- Persisting/comparing reports across runs (would be the first real justification for a database).
- Handling a vague question with a clarifying follow-up instead of the agent guessing at interpretation.
