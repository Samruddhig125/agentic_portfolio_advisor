from pydantic_ai import Agent 
from pydantic_ai.providers.ollama import OllamaProvider 
from dotenv import load_dotenv
load_dotenv() 


explanation_agent = Agent(
    model="ollama:llama3",  # Specifies Ollama provider with llama3 model (local inference)
    #provider=OllamaProvider(base_url="http://127.0.0.1:11434"),  # Commented out - uses default Ollama URL from env/model config
    system_prompt="""
    You are a financial advisor.

    Explain portfolio results in:
    - simple language           # Use everyday words, avoid jargon
    - human tone                # Conversational, friendly voice
    - clear insights            # Actionable takeaways and understanding
    """
)