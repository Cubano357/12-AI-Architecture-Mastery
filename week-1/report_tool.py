"""
Why this file exists:
This is the architectural decision that came out of tightening the source
requirement. Without this, the model would just write its final report as
free text, and checking "did it cite a real URL" would mean regex-parsing
prose - fragile, and never truly deterministic.

Instead, the model's FINAL action is a second tool call - submit_research_
brief - with a real JSON schema. That turns "the report" into a plain data
structure a few lines of Python can inspect, instead of a paragraph a
program has to interpret. Same tool-calling mechanism as search_web,
just used for structured output instead of external action - no new
dependency, no framework, just the second use of a mechanism the model
already has.
"""

TOOL_SCHEMA = {
    "name": "submit_research_brief",
    "description": (
        "Submit the final research brief. Call this exactly once, after "
        "you have gathered enough evidence with search_web. Every entry "
        "in 'sources' must be a URL that was actually returned by a "
        "search_web call in this conversation - never a URL you recall "
        "from training or assume exists."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "research_question": {
                "type": "string",
                "description": "Restate the question you were asked, in your own words, confirming your interpretation of it.",
            },
            "executive_summary": {
                "type": "string",
                "description": "2-3 sentence summary of the answer.",
            },
            "key_findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "finding": {"type": "string"},
                        "source_url": {
                            "type": "string",
                            "description": "The exact URL (from a search_web result) that supports this finding.",
                        },
                    },
                    "required": ["finding", "source_url"],
                },
                "description": "Each finding paired with the one source URL that supports it.",
            },
            "opportunities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Business opportunities the findings suggest.",
            },
            "risks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Risks, caveats, or reasons to distrust a finding.",
            },
            "sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "required": ["title", "url"],
                },
                "description": "Every source used, title + URL. Must all be real URLs returned by search_web.",
            },
        },
        "required": [
            "research_question",
            "executive_summary",
            "key_findings",
            "opportunities",
            "risks",
            "sources",
        ],
    },
}
