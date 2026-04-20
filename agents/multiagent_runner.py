import re
import json
import requests
import asyncio
from models import FinalAdvice, AIExplanation  # Data models for structured financial advice output
from logic import (
    calculate_risk_assessment,    # Calculates investor risk profile based on profile data
    generate_portfolio,           # Generates optimal asset allocation
    generate_scenarios,           # Creates what-if scenarios for portfolio performance
    generate_warnings,            # Identifies potential risks and issues
    generate_next_steps,          # Provides actionable next steps
    calculate_confidence_score,   # Computes confidence in the recommendation
)
from dotenv import load_dotenv    # Loads environment variables from .env file


# AGENT IMPORTS 
from .planner_agent import planner_agent      # AI agent for planning analysis workflow
from .explanation_agent import explanation_agent  # AI agent for generating user-friendly explanations


load_dotenv()  # Load environment variables (API keys, URLs, etc.)


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"  # Local Ollama API endpoint
OLLAMA_MODEL = "llama3"  # LLM model used for natural language explanations


# -----------------------------
# OLLAMA CALL (SYNC )
# -----------------------------
def _call_ollama(prompt: str) -> str:
    """Makes synchronous HTTP request to local Ollama API to generate LLM response.
    
    Args:
        prompt: Text prompt for the language model
        
    Returns:
        Raw response text from Ollama
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,  # Non-streaming response for simpler parsing
        "options": {
            "temperature": 0.3,    # Low temperature for consistent, deterministic output
            "num_predict": 600,    # Limit response length
        }
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)  # 2-minute timeout
    response.raise_for_status()  # Raise exception for HTTP errors
    return response.json()["response"].strip()  # Extract and clean response text


# -----------------------------
# PARSING HELPERS
# -----------------------------
def _extract_string(text: str, key: str, fallback: str = "") -> str:
    """Extracts string value from raw LLM response using regex pattern matching.
    
    Handles JSON-like key-value extraction when JSON parsing fails.
    """
    pattern = rf'"{key}"\s*:\s*"(.*?)"(?=\s*[,}}])'  # Regex for JSON string values
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else fallback


def _extract_list(text: str, key: str, fallback: list = None) -> list:
    """Extracts array values from raw LLM response using regex.
    
    Finds quoted strings within JSON array notation.
    """
    pattern = rf'"{key}"\s*:\s*\[(.*?)\]'  # Regex for JSON array values
    match = re.search(pattern, text, re.DOTALL)
    if match:
        items = re.findall(r'"(.*?)"', match.group(1), re.DOTALL)
        if items:
            return [i.strip() for i in items]
    return fallback or []


def _parse_llm_response(raw: str, profile, risk, portfolio, warnings) -> dict:
    """Robust JSON parser for LLM responses with fallback extraction.
    
    1. Cleans markdown code blocks
    2. Extracts JSON substring
    3. Fixes common JSON formatting issues
    4. Falls back to regex extraction if parsing fails
    """
    clean = raw.strip()

    # Step 1: Handle markdown code blocks (```json ...)
    if "```" in clean:
        parts = clean.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()  
            if part.startswith("{"):
                clean = part
                break

    # Step 2: Extract JSON object boundaries
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start != -1 and end > start:
        clean = clean[start:end]

    # Step 3: Fix common JSON syntax errors
    clean = re.sub(r',\s*([}\]])', r'\1', clean)  # Remove trailing commas
    clean = clean.replace('\u201c', '"').replace('\u201d', '"')  # Fix smart quotes
    clean = re.sub(
        r'(?<=: ")(.*?)(?=")',
        lambda m: m.group(0).replace('\n', ' '),  # Flatten newlines in strings
        clean,
        flags=re.DOTALL
    )

    # Step 4: Try JSON parsing, fallback to regex extraction
    try:
        return json.loads(clean)
    except Exception:
        pass

    # Fallback: Extract fields using regex with context-aware defaults
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
    """Generates human-readable financial advice using LLM.
    
    Creates structured prompt with investor context and parses response.
    """
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
# ASYNC CORE RUNNER
# -----------------------------
async def _run_multi_agent_async(user_input: str) -> dict:
    """Main async orchestrator combining AI agents + deterministic logic.
    
    Workflow:
    1. AI Planner Agent (creates analysis plan)
    2. Deterministic financial calculations
    3. LLM explanation generation
    4. AI Explanation Agent (enhances plain language)
    5. Structured output assembly
    """
    from parser import parse_profile_text  # Parses user input into investor profile

    # 1. Planner Agent (async) - generates analysis plan, gracefully handles failures
    try:
        plan = await planner_agent.run(user_input)
        plan_text = str(plan)
    except:
        plan_text = "Deterministic analysis pipeline executed."

    # 2. core financial calculations
    profile = parse_profile_text(user_input)           # Parse investor profile
    risk = calculate_risk_assessment(profile)          # Risk profiling
    portfolio = generate_portfolio(profile, risk)      # Asset allocation
    scenarios = generate_scenarios(profile, portfolio) # Performance scenarios
    warnings = generate_warnings(profile, risk)        # Risk warnings
    next_steps = generate_next_steps(profile)          # Action items
    confidence_score = calculate_confidence_score(profile, warnings)  # Quality score

    # 3. LLM explanation (sync) - natural language wrapper
    parsed = _get_ai_explanation(profile, risk, portfolio, warnings)

    # 4. Explanation Agent - enhances plain language explanation
    try:
        explanation_output = await explanation_agent.run(parsed["plain_explanation"])
        explanation_text = str(explanation_output)
    except:
        explanation_text = parsed.get("plain_explanation")

    # 5. Build structured output combining all components
    ai_explanation = AIExplanation(
        advisor_summary=parsed["advisor_summary"],
        allocation_explanation=parsed["allocation_explanation"],
        risk_justification=parsed["risk_justification"],
        improvement_suggestions=parsed["improvement_suggestions"],
        advisor_note=parsed["advisor_note"],
    )

    # Merge deterministic + AI suggestions (deduplicated)
    combined_next_steps = next_steps[:]
    for s in ai_explanation.improvement_suggestions:
        if s not in combined_next_steps:
            combined_next_steps.append(s)

    # Final structured financial advice object
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
        "plan": plan_text,           # AI planning output
        "finance": finance_output,   # Complete financial analysis
        "explanation": explanation_text,  # Enhanced plain language
    }


# -----------------------------
# SYNC WRAPPER 
# -----------------------------
def run_multi_agent(user_input: str) -> dict:
    """Synchronous entry point - converts async orchestrator to sync interface.
    
    Usage: result = run_multi_agent("I'm 35, moderate risk, 10yr horizon")
    """
    return asyncio.run(_run_multi_agent_async(user_input))