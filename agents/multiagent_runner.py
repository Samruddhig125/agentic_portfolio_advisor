import re
import json
import requests
from models import FinalAdvice, AIExplanation
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

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3"


def _call_ollama(prompt: str) -> str:
    """Call local Ollama llama3 and return raw response text."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,      # lower = more predictable output
            "num_predict": 600,
        }
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["response"].strip()


def _extract_string(text: str, key: str, fallback: str = "") -> str:
    """Extract a string value from JSON-like text using regex."""
    pattern = rf'"{key}"\s*:\s*"(.*?)"(?=\s*[,}}])'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return fallback


def _extract_list(text: str, key: str, fallback: list = None) -> list:
    """Extract a list of strings from JSON-like text using regex."""
    pattern = rf'"{key}"\s*:\s*\[(.*?)\]'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        items_raw = match.group(1)
        items = re.findall(r'"(.*?)"', items_raw, re.DOTALL)
        if items:
            return [i.strip() for i in items]
    return fallback or []


def _parse_llm_response(raw: str, profile, risk, portfolio, warnings) -> dict:
    """
    Robustly parse llama3 output.
    First tries json.loads, falls back to regex field extraction,
    falls back to asking the model field-by-field.
    """
    # Clean up common llama3 issues
    clean = raw.strip()

    # Strip markdown fences
    if "```" in clean:
        parts = clean.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                clean = part
                break

    # Find the outermost JSON object
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start != -1 and end > start:
        clean = clean[start:end]

    # Fix common llama3 JSON issues:
    # 1. Remove trailing commas before } or ]
    clean = re.sub(r',\s*([}\]])', r'\1', clean)
    # 2. Replace smart quotes
    clean = clean.replace('\u201c', '"').replace('\u201d', '"')
    # 3. Remove newlines inside string values
    clean = re.sub(r'(?<=: ")(.*?)(?=")', lambda m: m.group(0).replace('\n', ' '), clean, flags=re.DOTALL)

    # Try standard JSON parse first
    try:
        return json.loads(clean)
    except Exception:
        pass

    # Fallback: extract each field individually with regex
    investor_type = risk.investor_type
    result = {
        "advisor_summary": _extract_string(raw, "advisor_summary",
            f"{profile.name} is a {investor_type} investor with a {profile.investment_horizon_years}-year horizon targeting {profile.financial_goal}."),
        "allocation_explanation": _extract_list(raw, "allocation_explanation", [
            f"Equity at {portfolio.equity}% suits the {investor_type} profile.",
            f"Bonds and cash at {portfolio.bonds_debt + portfolio.cash}% provide stability.",
            f"Gold at {portfolio.gold}% acts as an inflation hedge.",
        ]),
        "risk_justification": _extract_string(raw, "risk_justification",
            f"A {investor_type} profile fits given the risk score of {risk.risk_score} and {profile.investment_horizon_years}-year horizon."),
        "improvement_suggestions": _extract_list(raw, "improvement_suggestions", [
            "Build an emergency fund before increasing equity exposure.",
            "Review and rebalance the portfolio every 6-12 months.",
        ]),
        "advisor_note": _extract_string(raw, "advisor_note",
            "Disciplined, long-term investing aligned with your goals is the strongest path to financial security."),
        "plain_explanation": _extract_string(raw, "plain_explanation",
            f"Based on your profile, a {investor_type} portfolio has been recommended with "
            f"{portfolio.equity}% in equity and {portfolio.bonds_debt}% in bonds. "
            f"This balances growth and safety for your {profile.investment_horizon_years}-year {profile.financial_goal} goal. "
            f"Stay consistent and review annually."),
    }
    return result


def _get_ai_explanation(profile, risk, portfolio, warnings) -> dict:
    """Call Ollama once with a simple, structured prompt."""

    # Keep prompt short and simple — llama3 struggles with long complex prompts
    prompt = f"""You are a financial advisor. Return ONLY a JSON object, nothing else.

Investor: {profile.name}, age {profile.age}, goal: {profile.financial_goal}, horizon: {profile.investment_horizon_years} years
Risk type: {risk.investor_type} (score {risk.risk_score})
Portfolio: Equity {portfolio.equity}%, MF {portfolio.mutual_funds_etfs}%, Bonds {portfolio.bonds_debt}%, Gold {portfolio.gold}%, Cash {portfolio.cash}%

Return this JSON with short values (no newlines inside strings):
{{
  "advisor_summary": "2 sentence summary for {profile.name}",
  "allocation_explanation": ["equity reason", "bonds reason", "gold reason"],
  "risk_justification": "why {risk.investor_type} fits",
  "improvement_suggestions": ["suggestion 1", "suggestion 2"],
  "advisor_note": "one closing sentence",
  "plain_explanation": "3 simple sentences explaining the portfolio"
}}

JSON only, no other text:"""

    raw = _call_ollama(prompt)
    return _parse_llm_response(raw, profile, risk, portfolio, warnings)


def run_multi_agent(user_input: str) -> dict:
    from parser import parse_profile_text

    # Deterministic layer
    profile = parse_profile_text(user_input)
    risk = calculate_risk_assessment(profile)
    portfolio = generate_portfolio(profile, risk)
    scenarios = generate_scenarios(profile, portfolio)
    warnings = generate_warnings(profile, risk)
    next_steps = generate_next_steps(profile)
    confidence_score = calculate_confidence_score(profile, warnings)

    # Single Ollama call
    parsed = _get_ai_explanation(profile, risk, portfolio, warnings)

    ai_explanation = AIExplanation(
        advisor_summary=parsed["advisor_summary"],
        allocation_explanation=parsed["allocation_explanation"],
        risk_justification=parsed["risk_justification"],
        improvement_suggestions=parsed["improvement_suggestions"],
        advisor_note=parsed["advisor_note"],
    )

    combined_next_steps = next_steps[:]
    for s in ai_explanation.improvement_suggestions:
        if s not in combined_next_steps:
            combined_next_steps.append(s)

    finance_output = FinalAdvice(
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

    return {
        "plan": f"Deterministic analysis complete. Investor type: {risk.investor_type}, Score: {risk.risk_score}.",
        "finance": finance_output,
        "explanation": parsed.get("plain_explanation", ai_explanation.advisor_summary),
    }