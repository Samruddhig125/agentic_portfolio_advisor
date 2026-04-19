from agents.finance_agent import finance_agent
from agents.explanation_agent import explanation_agent
from agents.planner_agent import planner_agent
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai import Agent
from dotenv import load_dotenv
load_dotenv()


def run_multi_agent(user_input: str):

    # Step 1: Planning
    plan = planner_agent.run_sync(user_input).output

    # Step 2: Finance computation
    finance_output = finance_agent.run_sync(
        user_input,
        tool_choice="run_full_analysis"
    ).output

    # Step 3: Explanation
    explanation = explanation_agent.run_sync(
        f"Explain this portfolio clearly: {finance_output}"
    ).output

    return {
        "plan": plan,
        "finance": finance_output,
        "explanation": explanation,
    }