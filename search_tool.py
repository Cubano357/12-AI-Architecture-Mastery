"""
Why this file exists:
This is the ONE tool the agent has. It has exactly two jobs: (1) describe
itself to Claude in the shape Claude's tool-use API expects (TOOL_SCHEMA),
and (2) actually call Tavily and return real results (run_search). Keeping
these together, and keeping this the *only* file that knows Tavily exists,
means swapping search providers later (Brave, SerpAPI, whatever) only ever
touches this one file - the agent loop and the rest of the system never
know or care which provider is behind "search_web".
"""
import requests

from config import get_tavily_api_key

TAVILY_ENDPOINT = "https://api.tavily.com/search"

# This is what Claude actually sees when deciding whether and how to call
# the tool. The description is doing real work here - it's the only
# "instruction" the model gets about when this tool is useful and what
# a good query looks like.
TOOL_SCHEMA = {
    "name": "search_web",
    "description": (
        "Search the live web for current, real information. Use this to "
        "find facts, competitors, reviews, news, or market data needed to "
        "answer the research question. Returns a list of real results, "
        "each with a title, URL, and a short content snippet. Only cite "
        "URLs that actually appear in a search_web result - never invent "
        "a source."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A focused search query - not the whole research question verbatim, but a specific angle of it.",
            }
        },
        "required": ["query"],
    },
}


def run_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Calls Tavily for real and returns a plain list of
    {"title": str, "url": str, "content": str} dicts.

    Deliberately returns an empty list (not an exception) on a graceful
    "no results" response - a search that finds nothing is a normal
    outcome the agent needs to reason about (Failure Scenario: "search
    returns zero results"), not a crash. Network/auth errors DO raise,
    since those are the agent's caller's problem to surface honestly,
    not something to silently paper over.
    """
    response = requests.post(
        TAVILY_ENDPOINT,
        json={
            "api_key": get_tavily_api_key(),
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            }
        )
    return results
