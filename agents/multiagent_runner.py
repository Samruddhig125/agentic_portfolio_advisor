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

# ✅ SAFE AGENT IMPORTS (relative)
from .planner_agent import planner_agent
from .explanation_agent import explanation_agent

load_dotenv()

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3"


# -----------------------------
# DIRECT OLLAMA CALL (WORKING)
# -----------------------------
def _call_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 600,
        }
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["response"].strip()


# -----------------------------
# PARSING HELPERS (UNCHANGED)
# -----------------------------
def _extract_string(text: str, key: str, fallback: str = "") -> str:
    pattern = rf'"{key}"\s*:\s*"(.*?)"(?=\s*[,}}])'
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else fallback


def _extract_list(text: str, key: str, fallback: list = None) -> list:
    pattern = rf'"{key}"\s*:\s*\[(.*?)\]'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        items = re.findall(r'"(.*?)"', match.group(1), re.DOTALL)
        if items:
            return [i.strip() for i in items]
    return fallback or []


def _parse_llm_response(raw: str, profile, risk, portfolio, warnings) -> dict:
    clean = raw.strip()

    if "```" in clean:
        parts = clean.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                clean = part
                break

    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start != -1 and end > start:
        clean = clean[start:end]

    clean = re.sub(r',\s*([}\]])', r'\1', clean)
    clean = clean.replace('\u201c', '"').replace('\u201d', '"')
    clean = re.sub(
        r'(?<=: ")(.*?)(?=")',
        lambda m: m.group(0).replace('\n', ' '),
        clean,
        flags=re.DOTALL
    )

    try:
        return json.loads(clean)
    except Exception:
        pass

    investor_type = risk.investor_type
    return {
        "advisor_summary": _extract_string(raw, "advisor_summary",
            f"{profile.name} is a {investor_type} investor."),
        "allocation_explanation": _extract_list(raw, "allocation_explanation", [
            f"Equity at {portfolio.equity}% suits the profile.",
            f"Bonds at {portfolio.bonds_debt}% provide stability.",
            f"Gold at {portfolio.gold}% hedges inflation.",
        ]),
        "risk_justification": _extract_string(raw, "risk_justification",
            f"{investor_type} fits score {risk.risk_score}."),
        "improvement_suggestions": _extract_list(raw, "improvement_suggestions", [
            "Review portfolio regularly",
            "Maintain emergency fund",
        ]),
        "advisor_note": _extract_string(raw, "advisor_note",
            "Stay disciplined."),
        "plain_explanation": _extract_string(raw, "plain_explanation",
            "Balanced portfolio recommended."),
    }


def _get_ai_explanation(profile, risk, portfolio, warnings) -> dict:
    prompt = f"""You are a financial advisor. Return ONLY JSON.

Investor: {profile.name}, age {profile.age}, goal: {profile.financial_goal}, horizon: {profile.investment_horizon_years} years
Risk type: {risk.investor_type} (score {risk.risk_score})
Portfolio: Equity {portfolio.equity}%, MF {portfolio.mutual_funds_etfs}%, Bonds {portfolio.bonds_debt}%, Gold {portfolio.gold}%, Cash {portfolio.cash}%

{{
  "advisor_summary": "2 sentence summary",
  "allocation_explanation": ["reason1", "reason2", "reason3"],
  "risk_justification": "why this risk fits",
  "improvement_suggestions": ["suggestion1", "suggestion2"],
  "advisor_note": "closing note",
  "plain_explanation": "simple explanation"
}}"""

    raw = _call_ollama(prompt)
    return _parse_llm_response(raw, profile, risk, portfolio, warnings)


# -----------------------------
# 🚀 FINAL MULTI-AGENT RUNNER
# -----------------------------
def run_multi_agent(user_input: str) -> dict:
    from parser import parse_profile_text

    # 🧠 1. Planner Agent (SAFE)
    try:
        plan = planner_agent.run(user_input)
        plan_text = str(plan)
    except:
        plan_text = "Deterministic analysis pipeline executed."

    # ⚙️ 2. Deterministic Core (UNCHANGED)
    profile = parse_profile_text(user_input)
    risk = calculate_risk_assessment(profile)
    portfolio = generate_portfolio(profile, risk)
    scenarios = generate_scenarios(profile, portfolio)
    warnings = generate_warnings(profile, risk)
    next_steps = generate_next_steps(profile)
    confidence_score = calculate_confidence_score(profile, warnings)

    # 🤖 3. Your original LLM explanation
    parsed = _get_ai_explanation(profile, risk, portfolio, warnings)

    # 🧾 4. Explanation Agent (optional enhancement)
    try:
        explanation_output = explanation_agent.run(parsed["plain_explanation"])
        explanation_text = str(explanation_output)
    except:
        explanation_text = parsed.get("plain_explanation")

    # 🧱 5. Build structured output
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

    # 📦 FINAL RESPONSE
    return {
        "plan": plan_text,
        "finance": finance_output,
        "explanation": explanation_text,
    }