from models import UserProfile, RiskAssessment, PortfolioAllocation, ScenarioOutcome


def calculate_risk_assessment(profile: UserProfile) -> RiskAssessment:
    score = 50
    rationale = []

    # Age-based adjustment
    if profile.age < 30:
        score += 10
        rationale.append("Young age allows greater recovery time and supports moderate-to-high growth exposure.")
    elif 30 <= profile.age <= 50:
        rationale.append("Mid-career age supports balanced risk-taking with stability.")
    else:
        score -= 10
        rationale.append("Higher age reduces portfolio risk capacity and favors capital preservation.")

    # Horizon-based adjustment
    if profile.investment_horizon_years >= 10:
        score += 15
        rationale.append("Long investment horizon supports growth-oriented assets.")
    elif 5 <= profile.investment_horizon_years < 10:
        score += 5
        rationale.append("Medium-term horizon allows a balanced mix of growth and safety.")
    elif profile.investment_horizon_years <= 3:
        score -= 15
        rationale.append("Short investment horizon requires better capital protection and liquidity.")

    # Risk appetite adjustment
    if profile.risk_appetite == "high":
        score += 20
        rationale.append("User explicitly prefers high risk.")
    elif profile.risk_appetite == "medium":
        rationale.append("User has moderate risk tolerance.")
    elif profile.risk_appetite == "low":
        score -= 20
        rationale.append("User explicitly prefers low risk.")

    # Emergency fund adjustment
    if not profile.has_emergency_fund:
        score -= 15
        rationale.append("Lack of emergency fund reduces ability to take investment risk.")

    # Liability adjustment
    if profile.liabilities > profile.current_savings:
        score -= 10
        rationale.append("High liabilities compared to savings suggest caution.")
    elif profile.liabilities == 0:
        score += 5
        rationale.append("No liabilities improve financial flexibility.")

    # Expense pressure adjustment
    expense_ratio = profile.monthly_expenses / profile.monthly_income
    if expense_ratio > 0.8:
        score -= 10
        rationale.append("High expense burden reduces sustainable investment risk capacity.")
    elif expense_ratio < 0.5:
        score += 5
        rationale.append("Healthy savings capacity supports disciplined long-term investing.")

    # Liquidity need adjustment
    if profile.liquidity_need == "high":
        score -= 10
        rationale.append("High liquidity need reduces suitability for illiquid or volatile allocation.")
    elif profile.liquidity_need == "low":
        score += 5
        rationale.append("Low liquidity need allows stronger long-term allocation.")

    # Goal-based adjustment
    if profile.financial_goal == "retirement" and profile.investment_horizon_years >= 10:
        score += 5
        rationale.append("Retirement goal with long horizon supports compounding-oriented growth assets.")
    elif profile.financial_goal in ["home purchase", "education"] and profile.investment_horizon_years <= 5:
        score -= 5
        rationale.append("A defined near-to-mid-term goal favors safer allocation.")
    elif profile.financial_goal == "emergency backup":
        score -= 15
        rationale.append("Emergency backup goal prioritizes liquidity and stability over growth.")

    score = max(0, min(score, 100))

    if score < 35:
        investor_type = "conservative"
    elif score < 55:
        investor_type = "balanced"
    elif score < 75:
        investor_type = "growth"
    else:
        investor_type = "aggressive"

    return RiskAssessment(
        risk_score=score,
        investor_type=investor_type,
        rationale=rationale,
    )


def generate_portfolio(profile: UserProfile, risk: RiskAssessment) -> PortfolioAllocation:
    if risk.investor_type == "conservative":
        allocation = {
            "equity": 10,
            "mutual_funds_etfs": 20,
            "bonds_debt": 40,
            "gold": 15,
            "cash": 15,
        }
    elif risk.investor_type == "balanced":
        allocation = {
            "equity": 20,
            "mutual_funds_etfs": 30,
            "bonds_debt": 25,
            "gold": 15,
            "cash": 10,
        }
    elif risk.investor_type == "growth":
        allocation = {
            "equity": 30,
            "mutual_funds_etfs": 35,
            "bonds_debt": 15,
            "gold": 10,
            "cash": 10,
        }
    else:
        allocation = {
            "equity": 40,
            "mutual_funds_etfs": 35,
            "bonds_debt": 10,
            "gold": 5,
            "cash": 10,
        }

    # Short horizon adjustment
    if profile.investment_horizon_years <= 3:
        allocation["equity"] = max(5, allocation["equity"] - 10)
        allocation["mutual_funds_etfs"] = max(15, allocation["mutual_funds_etfs"] - 5)
        allocation["bonds_debt"] += 10
        allocation["cash"] += 5

    # No emergency fund adjustment
    if not profile.has_emergency_fund:
        allocation["cash"] += 5
        allocation["equity"] = max(5, allocation["equity"] - 5)

    # High liquidity need adjustment
    if profile.liquidity_need == "high":
        allocation["cash"] += 5
        allocation["bonds_debt"] += 5
        allocation["equity"] = max(5, allocation["equity"] - 5)
        allocation["mutual_funds_etfs"] = max(10, allocation["mutual_funds_etfs"] - 5)

    # Goal-specific adjustment
    if profile.financial_goal == "retirement" and profile.investment_horizon_years >= 10:
        allocation["equity"] += 5
        allocation["mutual_funds_etfs"] += 5
        allocation["bonds_debt"] -= 5
        allocation["cash"] -= 5

    if profile.financial_goal == "emergency backup":
        allocation["cash"] += 10
        allocation["bonds_debt"] += 5
        allocation["equity"] = max(5, allocation["equity"] - 10)
        allocation["mutual_funds_etfs"] = max(10, allocation["mutual_funds_etfs"] - 5)

    # Liability-heavy adjustment
    if profile.liabilities > profile.current_savings:
        allocation["bonds_debt"] += 5
        allocation["cash"] += 5
        allocation["equity"] = max(5, allocation["equity"] - 5)
        allocation["gold"] = max(5, allocation["gold"] - 5)

    # Normalize to 100
    total = sum(allocation.values())
    diff = 100 - total
    allocation["cash"] += diff

    return PortfolioAllocation(**allocation)


def generate_scenarios(profile: UserProfile, portfolio: PortfolioAllocation) -> ScenarioOutcome:
    return ScenarioOutcome(
        market_crash=(
            f"In a sharp market correction, the portfolio may temporarily decline because of its "
            f"{portfolio.equity + portfolio.mutual_funds_etfs}% growth allocation. "
            f"However, {portfolio.bonds_debt}% in debt and {portfolio.cash}% in cash provide partial downside cushioning."
        ),
        inflation_shock=(
            f"If inflation rises, debt-heavy allocations may face pressure in real return terms. "
            f"The {portfolio.gold}% gold allocation and growth-oriented assets help provide inflation resilience."
        ),
        stable_growth=(
            f"In a stable market environment, this diversified allocation is designed to support gradual wealth creation "
            f"over a {profile.investment_horizon_years}-year horizon while maintaining some defensive balance."
        ),
        emergency_withdrawal=(
            f"If the investor needs funds urgently, the {portfolio.cash}% cash and {portfolio.bonds_debt}% debt portion "
            f"improve liquidity and reduce the chance of selling volatile assets at the wrong time."
        ),
    )


def generate_warnings(profile: UserProfile, risk: RiskAssessment) -> list[str]:
    warnings = []

    if not profile.has_emergency_fund:
        warnings.append("Build an emergency fund covering 3 to 6 months of expenses before increasing risk exposure.")

    if profile.liabilities > profile.current_savings:
        warnings.append("Liabilities exceed savings, so debt reduction should be considered alongside investing.")

    if profile.investment_horizon_years <= 3 and risk.investor_type in ["growth", "aggressive"]:
        warnings.append("Short-term horizon is not fully aligned with a highly growth-oriented risk profile.")

    if profile.monthly_expenses > profile.monthly_income * 0.8:
        warnings.append("High monthly expenses may reduce sustainable investment capacity.")

    if profile.financial_goal == "emergency backup":
        warnings.append("For an emergency-focused goal, capital safety and liquidity should take priority over return maximization.")

    if profile.liquidity_need == "high" and risk.investor_type in ["growth", "aggressive"]:
        warnings.append("High liquidity need may conflict with a more aggressive asset allocation style.")

    if not warnings:
        warnings.append("No major portfolio safety concerns detected based on the current profile.")

    return warnings


def generate_next_steps(profile: UserProfile) -> list[str]:
    steps = [
        "Review whether the suggested allocation matches your real-life comfort with volatility.",
        "Invest gradually instead of deploying the full amount at once if market timing is uncertain.",
        "Track your portfolio every 6 to 12 months and rebalance when needed.",
    ]

    if not profile.has_emergency_fund:
        steps.insert(0, "Create an emergency reserve before materially increasing exposure to risky assets.")

    if profile.liabilities > profile.current_savings:
        steps.append("Create a debt management plan so future investments are not stressed by liabilities.")

    if profile.financial_goal == "retirement":
        steps.append("Increase contributions periodically to benefit from long-term compounding.")

    if profile.financial_goal in ["education", "home purchase"]:
        steps.append("Shift gradually toward safer assets as the target date approaches.")

    return steps


def calculate_confidence_score(profile: UserProfile, warnings: list[str]) -> int:
    score = 92

    if not profile.has_emergency_fund:
        score -= 15

    if profile.liabilities > profile.current_savings:
        score -= 10

    if profile.investment_horizon_years <= 2:
        score -= 10

    if profile.monthly_expenses > profile.monthly_income * 0.8:
        score -= 7

    if profile.liquidity_need == "high":
        score -= 5

    if profile.financial_goal == "emergency backup":
        score -= 8

    score -= max(0, len(warnings) - 1) * 2

    return max(40, min(score, 95))