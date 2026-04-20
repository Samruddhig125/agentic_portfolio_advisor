import re
import requests
from models import UserProfile

def extract_number(text: str, field_name: str, default: float = 0):
    """Extracts numeric values from unstructured text using regex.
    
    Supports formats: 'age: 35', 'age=35', 'Age 35'
    """
    pattern = rf"{field_name}\s*[:=]?\s*(\d+)"  # Flexible field matching
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else default



def extract_text_value(text: str, field_name: str, default: str = ""):
    """Extracts categorical text values (risk, goals) from natural language."""
    pattern = rf"{field_name}\s*[:=]?\s*([A-Za-z ]+)"  # Matches words after field name
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip().lower() if match else default



def extract_bool(text: str, field_name: str, default: bool = False):
    """Extracts boolean values (yes/no, true/false) from text."""
    pattern = rf"{field_name}\s*[:=]?\s*(yes|true|no|false)"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return default
    value = match.group(1).lower()
    return value in ["yes", "true"]  # Flexible true equivalents



def parse_profile_text(raw_text: str) -> UserProfile:
    """Converts free-form text into validated UserProfile object.
    
    Supported input examples:
    - 'John, age 35, risk medium, retirement goal'
    - 'age=42 monthly income:75000 investment:100k'
    """
    # Extract name (fallback: "Investor")
    name_match = re.search(r"name\s*[:=]?\s*([A-Za-z ]+)", raw_text, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else "Investor"

    # Extract all numeric fields with sensible defaults
    age = int(extract_number(raw_text, "age", 25))  # Default young professional
    monthly_income = extract_number(raw_text, "monthly income", 50000)
    monthly_expenses = extract_number(raw_text, "monthly expenses", 20000)
    current_savings = extract_number(raw_text, "current savings", 100000)
    liabilities = extract_number(raw_text, "liabilities", 0)
    investment_amount = extract_number(raw_text, "investment amount", 50000)
    investment_horizon_years = int(extract_number(raw_text, "investment horizon", 5))

    # Extract categorical fields
    financial_goal = extract_text_value(raw_text, "financial goal", "wealth creation")
    risk_appetite = extract_text_value(raw_text, "risk appetite", "medium")
    liquidity_need = extract_text_value(raw_text, "liquidity need", "medium")
    has_emergency_fund = extract_bool(raw_text, "emergency fund", True)

    # Normalize to Pydantic model constraints
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

    # Return fully validated Pydantic model (triggers model validators)
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
    """Fetches raw text content from any HTTP URL (timeout protected)."""
    response = requests.get(url, timeout=10)  # 10s timeout
    response.raise_for_status()  # Raise for HTTP errors
    return response.text



def parse_profile_url(url: str) -> UserProfile:
    """End-to-end: fetch URL → parse text → validated profile."""
    raw_text = fetch_text_from_url(url)
    return parse_profile_text(raw_text)