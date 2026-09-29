"""
Why this file exists:
This is the actual "agent" - everything else in this project (search_tool,
report_tool, system_prompt, verification) is a resource this loop uses.
This is where the decision-making happens: give Claude the question and
both tools, let it decide when to search and when it has enough to answer,
and stop the instant it submits a structured brief.

The loop shape here - call the model, check stop_reason, execute any
tool_use blocks, feed results back, repeat - is the same shape every
tool-using agent has, regardless of how many tools it has or how complex
the tools are. Understanding THIS loop is understanding what "an agent"
actually is under the hood, before any framework puts a nicer name on it.
"""
import json

import anthropic

from config import get_anthropic_api_key
from system_prompt import SYSTEM_PROMPT
from search_tool import TOOL_SCHEMA as SEARCH_TOOL_SCHEMA, run_search
from report_tool import TOOL_SCHEMA as REPORT_TOOL_SCHEMA

MODEL = "claude-sonnet-5"

# A research question should resolve in 1-2 search calls. This cap exists
# so a model that gets stuck in a loop (e.g. searching endlessly without
# ever submitting a brief) fails loudly after a bounded number of rounds
# instead of running - and burning API cost - forever.
MAX_TOOL_ROUNDS = 6


def run_agent(research_question: str) -> tuple[dict, set[str]]:
    """
    Runs the full agent loop for one research question.

    Returns (brief, seen_urls):
    - brief: the structured dict Claude passed to submit_research_brief
    - seen_urls: every URL actually returned by search_web during this run -
      the ground truth that verification.py checks the brief's claimed
      sources against.
    """
    client = anthropic.Anthropic(api_key=get_anthropic_api_key())

    messages = [{"role": "user", "content": research_question}]
    seen_urls: set[str] = set()

    for round_number in range(MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[SEARCH_TOOL_SCHEMA, REPORT_TOOL_SCHEMA],
            messages=messages,
        )

        # Claude's full turn (any text plus any tool_use blocks) becomes
        # the next assistant message verbatim - this is how the SDK
        # expects tool-use conversations to be threaded.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            raise RuntimeError(
                f"Agent stopped without calling a tool (stop_reason={response.stop_reason}). "
                "The system prompt requires ending with submit_research_brief - "
                "check the prompt, or this may be a genuine model refusal worth reading response.content for."
            )

        tool_results = []
        submitted_brief = None

        # A single turn can contain more than one tool_use block (parallel
        # tool calls) - every one of them needs a matching tool_result
        # before the conversation can continue, so this loop collects all
        # of them before deciding what to do next.
        for block in response.content:
            if block.type != "tool_use":
                continue

            if block.name == "search_web":
                results = run_search(block.input["query"])
                for result in results:
                    seen_urls.add(result["url"])
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(results),
                    }
                )

            elif block.name == "submit_research_brief":
                submitted_brief = block.input
                # No tool_result needed: this ends the loop, so there is
                # no further turn that would need one to react to.

        if submitted_brief is not None:
            return submitted_brief, seen_urls

        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError(
        f"Agent did not submit a research brief within {MAX_TOOL_ROUNDS} tool-call rounds."
    )
