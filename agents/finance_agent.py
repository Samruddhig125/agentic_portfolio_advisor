from pydantic_ai.providers.ollama import OllamaProvider
from models import FinalAdvice, AIExplanation
from pydantic_ai import Agent
from dotenv import load_dotenv
load_dotenv()

finance_agent = Agent(
    model="ollama:llama3",
    #provider=OllamaProvider(base_url="http://127.0.0.1:11434"),
    output_type=FinalAdvice,
    system_prompt="""
    You are a financial computation agent.

    Always:
    - parse the user profile
    - calculate risk
    - generate portfolio
    - generate scenarios
    - generate warnings
    - generate next steps
    - compute confidence score

    Return structured output only.
    """
)