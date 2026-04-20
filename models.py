from pydantic import BaseModel, Field, model_validator  # Pydantic for data validation and structured models
from typing import Literal, List  # Type hints for strict typing and predefined values



class AIExplanation(BaseModel):
    """LLM-generated human-readable financial explanations."""
    advisor_summary: str = Field(
        ...,
        description="Personalized portfolio summary for the investor."
    )
    allocation_explanation: List[str] = Field(
        ...,
        description="Reason for each major allocation choice."
    )
    risk_justification: str = Field(
        ...,
        description="Why this risk profile suits the investor."
    )
    improvement_suggestions: List[str] = Field(
        ...,
        description="Suggestions to improve investment readiness."
    )
    advisor_note: str = Field(
        ...,
        description="A premium advisor-style concluding note."
    )



class UserProfile(BaseModel):
    """Complete investor financial profile with validation."""
    name: str = Field(..., min_length=2, max_length=50)  # Basic name validation
    age: int = Field(..., ge=18, le=80)  # Working age range
    monthly_income: float = Field(..., gt=0)  # Must be positive
    monthly_expenses: float = Field(..., ge=0)
    current_savings: float = Field(..., ge=0)
    liabilities: float = Field(..., ge=0)
    investment_amount: float = Field(..., gt=0)  # Investment capital
    investment_horizon_years: int = Field(..., ge=1, le=40)  # Realistic timeframes
    financial_goal: Literal[
        "wealth creation",
        "retirement",
        "education",
        "home purchase",
        "emergency backup",
    ]  # Predefined goals
    risk_appetite: Literal["low", "medium", "high"]  # Strict risk categories
    liquidity_need: Literal["low", "medium", "high"]
    has_emergency_fund: bool  # Critical safety check

    @model_validator(mode="after")
    def validate_financials(self):
        """Custom validation for financial realism."""
        if self.monthly_expenses > self.monthly_income * 2:
            raise ValueError(
                "Monthly expenses look unrealistically high compared to income."
            )
        if self.investment_amount > self.current_savings + (self.monthly_income * 6):
            raise ValueError(
                "Investment amount is too high for the given savings/income profile."
            )
        return self



class RiskAssessment(BaseModel):
    """Investor risk profile with quantitative score and qualitative type."""
    risk_score: int = Field(..., ge=0, le=100)  # 0-100 scale
    investor_type: Literal["conservative", "balanced", "growth", "aggressive"]
    rationale: List[str]  # Explanation of risk classification



class PortfolioAllocation(BaseModel):
    """Asset allocation percentages with 100% total validation."""
    equity: float = Field(..., ge=0, le=100)  # Stocks
    mutual_funds_etfs: float = Field(..., ge=0, le=100)  # Diversified funds
    bonds_debt: float = Field(..., ge=0, le=100)  # Fixed income
    gold: float = Field(..., ge=0, le=100)  # Inflation hedge
    cash: float = Field(..., ge=0, le=100)  # Liquidity

    @model_validator(mode="after")
    def total_must_equal_100(self):
        """Enforces portfolio must sum to exactly 100%."""
        total = (
            self.equity
            + self.mutual_funds_etfs
            + self.bonds_debt
            + self.gold
            + self.cash
        )
        if round(total, 2) != 100.0:
            raise ValueError(f"Portfolio allocation must total 100, got {total}")
        return self



class ScenarioOutcome(BaseModel):
    """What-if scenarios for portfolio stress testing."""
    market_crash: str      # Bear market performance
    inflation_shock: str   # High inflation impact
    stable_growth: str     # Normal market conditions
    emergency_withdrawal: str  # Liquidity crisis



class FinalAdvice(BaseModel):
    """Complete financial recommendation package."""
    summary: str  # Executive overview
    risk_assessment: RiskAssessment
    allocation: PortfolioAllocation
    reasons: List[str]  # Why this allocation
    scenario_analysis: ScenarioOutcome
    warnings: List[str]  # Red flags and cautions
    next_steps: List[str]  # Actionable recommendations
    confidence_score: int = Field(..., ge=0, le=100)  # Analysis quality (0-100)
    advisor_note: str  # Professional closing remarks
    ai_explanation: AIExplanation  # LLM-enhanced narrative