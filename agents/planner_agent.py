from pydantic_ai import Agent  
from pydantic_ai.providers.ollama import OllamaProvider 
from dotenv import load_dotenv 
load_dotenv()  


planner_agent = Agent(
    model="ollama:llama3",  # Local Ollama instance running Llama3 model
    #provider=OllamaProvider(base_url="http://127.0.0.1:11434"),  # Commented out - uses default Ollama config from env vars
    system_prompt="""
    You are a planning agent.

    Break financial analysis into steps:
    1. Parse input              # Extract age, goals, risk tolerance, horizon from user text
    2. Calculate risk           # Determine conservative/moderate/aggressive profile
    3. Generate portfolio       # Create asset allocation (equity/bonds/gold/cash)
    4. Explain results          # Generate human-readable analysis summary
    """
)