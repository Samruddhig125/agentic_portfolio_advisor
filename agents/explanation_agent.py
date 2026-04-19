from pydantic_ai import Agent
from pydantic_ai.providers.ollama import OllamaProvider
from dotenv import load_dotenv
load_dotenv()

explanation_agent = Agent(
    model="ollama:llama3",
    #provider=OllamaProvider(base_url="http://127.0.0.1:11434"),
    system_prompt="""
    You are a financial advisor.

    Explain portfolio results in:
    - simple language
    - human tone
    - clear insights
    """
)