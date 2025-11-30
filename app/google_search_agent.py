from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.google_search_tool import google_search
from google.genai import types

# Retry configuration for the Google LLM
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Dedicated Web Search Agent (tool-only)
google_search_agent = LlmAgent(
    name="google_search_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description=(
        "A utility agent that ONLY performs web searches for up-to-date "
        "information, trends, statistics, and recent facts."
    ),
    instruction="""
You are a supporting Web Search Agent.

Role:
- You are NOT the main tutor.
- You are only called by another agent when up-to-date, real-world information is needed.

Behavior:
- ALWAYS use the google_search tool to answer.
- Construct 1–3 focused search queries.
- Summarize the results concisely and factually.
- No teaching, no explanations, no greeting, no small talk.
- If search returns nothing useful, say so explicitly.

Output:
- Respond with a short factual summary suitable for another agent to show/explain to the user.
""",
    tools=[google_search],
)