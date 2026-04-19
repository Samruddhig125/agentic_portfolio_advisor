import os
from pydantic_ai import Agent
from pydantic_ai.providers.ollama import OllamaProvider

from models import UserProfile, FinalAdvice, AIExplanation
from logic import (
    calculate_risk_assessment,
    generate_portfolio,
    generate_scenarios,
    generate_warnings,
    generate_next_steps,
    calculate_confidence_score,
)
from dotenv import load_dotenv
load_dotenv()

explanation_agent = Agent(
    model="ollama:llama3",
    #provider=OllamaProvider(base_url="http://127.0.0.1:11434"),
    
    output_type=AIExplanation,
    system_prompt=(
        "You are an expert portfolio advisory AI for educational use. "
        "Generate professional, profile-specific, explainable investment guidance. "
        "Do not use vague generic statements. "
        "Explicitly connect the recommendation to the investor's age, income, expenses, savings, liabilities, "
        "investment horizon, financial goal, risk appetite, liquidity need, and emergency fund status. "
        "Do not guarantee returns. "
        "Do not recommend speculative or reckless behavior. "
        "Be precise, premium, analytical, and conservative in tone."
    ),
)


def build_advice(profile: UserProfile) -> FinalAdvice:
    risk = calculate_risk_assessment(profile)
    portfolio = generate_portfolio(profile, risk)
    scenarios = generate_scenarios(profile, portfolio)
    warnings = generate_warnings(profile, risk)
    next_steps = generate_next_steps(profile)
    confidence_score = calculate_confidence_score(profile, warnings)

    prompt = f"""
You are given a validated investor profile and a deterministic portfolio recommendation.

INVESTOR PROFILE
Name: {profile.name}
Age: {profile.age}
Monthly Income: {profile.monthly_income}
Monthly Expenses: {profile.monthly_expenses}
Current Savings: {profile.current_savings}
Liabilities: {profile.liabilities}
Investment Amount: {profile.investment_amount}
Investment Horizon: {profile.investment_horizon_years} years
Financial Goal: {profile.financial_goal}
Risk Appetite: {profile.risk_appetite}
Liquidity Need: {profile.liquidity_need}
Emergency Fund Available: {profile.has_emergency_fund}

DETERMINISTIC RISK ASSESSMENT
Risk Score: {risk.risk_score}
Investor Type: {risk.investor_type}
Rationale: {risk.rationale}

DETERMINISTIC PORTFOLIO ALLOCATION
Equity: {portfolio.equity}%
Mutual Funds / ETFs: {portfolio.mutual_funds_etfs}%
Bonds / Debt: {portfolio.bonds_debt}%
Gold: {portfolio.gold}%
Cash: {portfolio.cash}%

SYSTEM WARNINGS
{warnings}

Generate a structured advisory explanation in the required schema.

Requirements:
1. advisor_summary must be personalized and specific.
2. allocation_explanation must clearly justify the main allocation choices.
3. risk_justification must explain why the investor type fits this user.
4. improvement_suggestions must be practical and realistic.
5. advisor_note must sound premium, concise, and professional.
6. Do not mention JSON, schema, Pydantic, or internal implementation.
7. Do not promise profit or guaranteed returns.
"""

    ai_result = explanation_agent.run_sync(prompt)
    ai_explanation = ai_result.output

    combined_next_steps = next_steps[:]
    for suggestion in ai_explanation.improvement_suggestions:
        if suggestion not in combined_next_steps:
            combined_next_steps.append(suggestion)

    return FinalAdvice(
        summary=ai_explanation.advisor_summary,
        risk_assessment=risk,
        allocation=portfolio,
        reasons=ai_explanation.allocation_explanation,
        scenario_analysis=scenarios,
        warnings=warnings,
        next_steps=combined_next_steps,
        confidence_score=confidence_score,
        advisor_note=ai_explanation.advisor_note,
        ai_explanation=ai_explanation,
    )