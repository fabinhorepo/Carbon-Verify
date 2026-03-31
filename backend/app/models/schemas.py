"""Schemas Pydantic para validação e serialização de dados."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ─── Auth ────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str
    organization_name: str


# ─── Organization ────────────────────────────────────────────────────────

class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    plan: str
    api_key: Optional[str] = None

    class Config:
        from_attributes = True


# ─── User ────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    organization_id: int
    is_active: bool

    class Config:
        from_attributes = True


# ─── Carbon Project ─────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    project_type: str
    methodology: Optional[str] = None
    registry: Optional[str] = None
    country: str
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    proponent: Optional[str] = None
    total_credits_issued: int = 0
    total_credits_retired: int = 0
    total_credits_available: int = 0
    vintage_year: Optional[int] = None
    area_hectares: Optional[float] = None
    baseline_scenario: Optional[str] = None
    additionality_justification: Optional[str] = None
    monitoring_frequency: Optional[str] = None
    buffer_pool_percentage: Optional[float] = None

class ProjectResponse(BaseModel):
    id: int
    external_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    project_type: str
    methodology: Optional[str] = None
    registry: Optional[str] = None
    country: str
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    proponent: Optional[str] = None
    total_credits_issued: int
    total_credits_retired: int
    total_credits_available: int
    vintage_year: Optional[int] = None
    area_hectares: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Rating ──────────────────────────────────────────────────────────────

class RatingResponse(BaseModel):
    id: int
    project_id: int
    overall_score: float
    grade: str
    additionality_score: float
    permanence_score: float
    leakage_score: float
    mrv_score: float
    co_benefits_score: float
    governance_score: float
    baseline_integrity_score: float
    confidence_level: float
    explanation: Optional[str] = None
    risk_flags: Optional[list] = None
    rated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectWithRating(ProjectResponse):
    rating: Optional[RatingResponse] = None
    fraud_alert_count: int = 0


# ─── Fraud Alert ─────────────────────────────────────────────────────────

class FraudAlertResponse(BaseModel):
    id: int
    project_id: int
    project_name: Optional[str] = None
    alert_type: str
    severity: str
    status: str
    title: str
    description: str
    evidence: Optional[dict] = None
    recommendation: Optional[str] = None
    detection_method: Optional[str] = None
    confidence: float
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FraudAlertUpdate(BaseModel):
    status: Optional[str] = None
    review_notes: Optional[str] = None
    reviewed_by: Optional[str] = None


# ─── Portfolio ───────────────────────────────────────────────────────────

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None

class PortfolioResponse(BaseModel):
    id: int
    name: str
    organization_id: int
    description: Optional[str] = None
    total_credits: int
    total_value_eur: float
    avg_quality_score: float
    risk_exposure: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PositionCreate(BaseModel):
    credit_id: int
    quantity: int
    acquisition_price_eur: Optional[float] = None
    acquisition_date: Optional[datetime] = None
    planned_retirement_date: Optional[datetime] = None

class PositionResponse(BaseModel):
    id: int
    portfolio_id: int
    credit_id: int
    quantity: int
    acquisition_price_eur: Optional[float] = None
    acquisition_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Paginated Response ─────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── Dashboard Metrics ───────────────────────────────────────────────────

class DashboardMetrics(BaseModel):
    total_projects: int
    total_credits: int
    avg_quality_score: float
    grade_distribution: dict
    risk_summary: dict
    fraud_alerts_count: int
    fraud_alerts_by_severity: dict
    project_type_distribution: dict
    country_distribution: dict
    portfolio_value_eur: float

class PortfolioRecommendation(BaseModel):
    project_id: int
    project_name: str
    current_grade: str
    current_score: float
    action: str  # "sell", "hold", "buy_more"
    reason: str
    risk_level: str
    priority: int


# Atualizar referência forward
TokenResponse.model_rebuild()
