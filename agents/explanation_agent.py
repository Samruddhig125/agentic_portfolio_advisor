from pydantic_ai import Agent
from pydantic_ai.providers.ollama import OllamaProvider
from dotenv import load_dotenv
load_dotenv()

explanation_agent = Agent(
    "ollama:llama3.2:3b",
    system_prompt="""
    You are a financial advisor.

    Explain portfolio results in:
    - simple language
    - human tone
    - clear insights
    """
)