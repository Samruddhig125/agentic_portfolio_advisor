import re
import requests
from models import UserProfile


def extract_number(text: str, field_name: str, default: float = 0):
    pattern = rf"{field_name}\s*[:=]?\s*(\d+)"
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else default


def extract_text_value(text: str, field_name: str, default: str = ""):
    pattern = rf"{field_name}\s*[:=]?\s*([A-Za-z ]+)"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip().lower() if match else default


def extract_bool(text: str, field_name: str, default: bool = False):
    pattern = rf"{field_name}\s*[:=]?\s*(yes|true|no|false)"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return default
    value = match.group(1).lower()
    return value in ["yes", "true"]


def parse_profile_text(raw_text: str) -> UserProfile:
    name_match = re.search(r"name\s*[:=]?\s*([A-Za-z ]+)", raw_text, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else "Investor"

    age = int(extract_number(raw_text, "age", 25))
    monthly_income = extract_number(raw_text, "monthly income", 50000)
    monthly_expenses = extract_number(raw_text, "monthly expenses", 20000)
    current_savings = extract_number(raw_text, "current savings", 100000)
    liabilities = extract_number(raw_text, "liabilities", 0)
    investment_amount = extract_number(raw_text, "investment amount", 50000)
    investment_horizon_years = int(extract_number(raw_text, "investment horizon", 5))

    financial_goal = extract_text_value(raw_text, "financial goal", "wealth creation")
    risk_appetite = extract_text_value(raw_text, "risk appetite", "medium")
    liquidity_need = extract_text_value(raw_text, "liquidity need", "medium")
    has_emergency_fund = extract_bool(raw_text, "emergency fund", True)

    allowed_goals = [
        "wealth creation",
        "retirement",
        "education",
        "home purchase",
        "emergency backup",
    ]
    if financial_goal not in allowed_goals:
        financial_goal = "wealth creation"

    if risk_appetite not in ["low", "medium", "high"]:
        risk_appetite = "medium"

    if liquidity_need not in ["low", "medium", "high"]:
        liquidity_need = "medium"

    return UserProfile(
        name=name,
        age=age,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        current_savings=current_savings,
        liabilities=liabilities,
        investment_amount=investment_amount,
        investment_horizon_years=investment_horizon_years,
        financial_goal=financial_goal,
        risk_appetite=risk_appetite,
        liquidity_need=liquidity_need,
        has_emergency_fund=has_emergency_fund,
    )


def fetch_text_from_url(url: str) -> str:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


def parse_profile_url(url: str) -> UserProfile:
    raw_text = fetch_text_from_url(url)
    return parse_profile_text(raw_text)