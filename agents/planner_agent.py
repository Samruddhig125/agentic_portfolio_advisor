from pydantic_ai import Agent
from pydantic_ai.providers.ollama import OllamaProvider
from dotenv import load_dotenv
load_dotenv()

planner_agent = Agent(
    "ollama:llama3.2:3b",
    system_prompt="""
    You are a planning agent.

    Break financial analysis into steps:
    1. Parse input
    2. Calculate risk
    3. Generate portfolio
    4. Explain results
    """
)