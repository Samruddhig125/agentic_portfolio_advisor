from pydantic_ai import Agent
from pydantic_ai.providers.ollama import OllamaProvider
from dotenv import load_dotenv
load_dotenv()

planner_agent = Agent(
    model="ollama:llama3",
    #provider=OllamaProvider(base_url="http://127.0.0.1:11434"),
    system_prompt="""
    You are a planning agent.

    Break financial analysis into steps:
    1. Parse input
    2. Calculate risk
    3. Generate portfolio
    4. Explain results
    """
)