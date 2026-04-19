from pydantic import BaseModel, Field, model_validator
from typing import Literal, List


class AIExplanation(BaseModel):
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
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., ge=18, le=80)
    monthly_income: float = Field(..., gt=0)
    monthly_expenses: float = Field(..., ge=0)
    current_savings: float = Field(..., ge=0)
    liabilities: float = Field(..., ge=0)
    investment_amount: float = Field(..., gt=0)
    investment_horizon_years: int = Field(..., ge=1, le=40)
    financial_goal: Literal[
        "wealth creation",
        "retirement",
        "education",
        "home purchase",
        "emergency backup",
    ]
    risk_appetite: Literal["low", "medium", "high"]
    liquidity_need: Literal["low", "medium", "high"]
    has_emergency_fund: bool

    @model_validator(mode="after")
    def validate_financials(self):
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
    risk_score: int = Field(..., ge=0, le=100)
    investor_type: Literal["conservative", "balanced", "growth", "aggressive"]
    rationale: List[str]


class PortfolioAllocation(BaseModel):
    equity: float = Field(..., ge=0, le=100)
    mutual_funds_etfs: float = Field(..., ge=0, le=100)
    bonds_debt: float = Field(..., ge=0, le=100)
    gold: float = Field(..., ge=0, le=100)
    cash: float = Field(..., ge=0, le=100)

    @model_validator(mode="after")
    def total_must_equal_100(self):
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
    market_crash: str
    inflation_shock: str
    stable_growth: str
    emergency_withdrawal: str


class FinalAdvice(BaseModel):
    summary: str
    risk_assessment: RiskAssessment
    allocation: PortfolioAllocation
    reasons: List[str]
    scenario_analysis: ScenarioOutcome
    warnings: List[str]
    next_steps: List[str]
    confidence_score: int = Field(..., ge=0, le=100)
    advisor_note: str
    ai_explanation: AIExplanation