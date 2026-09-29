"""
Why this file exists:
Every credential the agent needs (Anthropic, Tavily) is read from the
environment, never hardcoded and never logged. This is the one place that
knows *where* keys come from, so the rest of the codebase just asks for
"the Anthropic key" without caring whether it's a local .env file, a CI
secret, or a cloud secret manager. Swap the source later without touching
agent logic - that's the whole point of centralizing it here.
"""
import os


class ConfigError(RuntimeError):
    """Raised when a required credential is missing, with a clear fix."""


def get_anthropic_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ConfigError(
            "ANTHROPIC_API_KEY is not set. Get one from console.anthropic.com "
            "and set it as an environment variable (or put it in a .env file "
            "and load it before running)."
        )
    return key


def get_tavily_api_key() -> str:
    key = os.environ.get("TAVILY_API_KEY")
    if not key:
        raise ConfigError(
            "TAVILY_API_KEY is not set. Get one from tavily.com and set it "
            "as an environment variable."
        )
    return key
