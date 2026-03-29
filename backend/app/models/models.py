"""Modelos SQLAlchemy para o MVP Carbon Verify."""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


# ─── Enums ───────────────────────────────────────────────────────────────

class RatingGrade(str, enum.Enum):
    AAA = "AAA"
    AA = "AA"
    A = "A"
    BBB = "BBB"
    BB = "BB"
    B = "B"
    CCC = "CCC"
    CC = "CC"
    C = "C"
    D = "D"


class ProjectType(str, enum.Enum):
    REDD = "REDD+"
    ARR = "ARR"
    RENEWABLE_ENERGY = "Renewable Energy"
    COOKSTOVE = "Cookstove"
    METHANE = "Methane Avoidance"
    BLUE_CARBON = "Blue Carbon"
    BIOCHAR = "Biochar"
    DAC = "Direct Air Capture"
    OTHER = "Other"


class FraudSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


# ─── Organization (Multi-tenant) ────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    api_key = Column(String(500), nullable=True)
    plan = Column(String(50), default="free")
    rate_limit = Column(Integer, default=60)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    users = relationship("User", back_populates="organization")
    portfolios = relationship("Portfolio", back_populates="organization")


# ─── User ────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.ANALYST)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    organization = relationship("Organization", back_populates="users")


# ─── Carbon Project ─────────────────────────────────────────────────────

class CarbonProject(Base):
    __tablename__ = "carbon_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(100), nullable=True, unique=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    project_type = Column(SQLEnum(ProjectType), nullable=False)
    methodology = Column(String(255), nullable=True)
    registry = Column(String(100), nullable=True)  # Verra, Gold Standard, etc.
    country = Column(String(100), nullable=False)
    region = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    proponent = Column(String(255), nullable=True)
    total_credits_issued = Column(Integer, default=0)
    total_credits_retired = Column(Integer, default=0)
    total_credits_available = Column(Integer, default=0)
    vintage_year = Column(Integer, nullable=True)
    area_hectares = Column(Float, nullable=True)
    
    # Dados de baseline e monitoramento
    baseline_scenario = Column(Text, nullable=True)
    additionality_justification = Column(Text, nullable=True)
    monitoring_frequency = Column(String(100), nullable=True)
    buffer_pool_percentage = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    credits = relationship("CarbonCredit", back_populates="project")
    rating = relationship("ProjectRating", back_populates="project", uselist=False)
    fraud_alerts = relationship("FraudAlert", back_populates="project")


# ─── Carbon Credit ──────────────────────────────────────────────────────

class CarbonCredit(Base):
    __tablename__ = "carbon_credits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    serial_number = Column(String(255), nullable=True, unique=True)
    project_id = Column(Integer, ForeignKey("carbon_projects.id"), nullable=False)
    vintage_year = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    status = Column(String(50), default="active")  # active, retired, cancelled
    issuance_date = Column(DateTime, nullable=True)
    retirement_date = Column(DateTime, nullable=True)
    price_usd = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=utcnow)

    project = relationship("CarbonProject", back_populates="credits")
    positions = relationship("PortfolioPosition", back_populates="credit")


# ─── Módulo 1: Rating de Qualidade ──────────────────────────────────────

class ProjectRating(Base):
    __tablename__ = "project_ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("carbon_projects.id"), nullable=False, unique=True)
    
    # Rating final
    overall_score = Column(Float, nullable=False)  # 0-100
    grade = Column(SQLEnum(RatingGrade), nullable=False)
    
    # Sub-scores por dimensão (0-100)
    additionality_score = Column(Float, default=0)
    permanence_score = Column(Float, default=0)
    leakage_score = Column(Float, default=0)
    mrv_score = Column(Float, default=0)  # Measurement, Reporting, Verification
    co_benefits_score = Column(Float, default=0)
    governance_score = Column(Float, default=0)
    baseline_integrity_score = Column(Float, default=0)
    
    # Metadados
    methodology_version = Column(String(50), default="v1.0")
    confidence_level = Column(Float, default=0.0)  # 0-1
    explanation = Column(Text, nullable=True)
    risk_flags = Column(JSON, nullable=True)  # Lista de flags de risco
    
    rated_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    project = relationship("CarbonProject", back_populates="rating")


# ─── Módulo 2: Fraud Detection ──────────────────────────────────────────

class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("carbon_projects.id"), nullable=False)
    
    alert_type = Column(String(100), nullable=False)
    severity = Column(SQLEnum(FraudSeverity), nullable=False)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.OPEN)
    
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=True)
    recommendation = Column(Text, nullable=True)
    
    # Dados de detecção
    detection_method = Column(String(100), nullable=True)  # rule_based, anomaly_detection
    confidence = Column(Float, default=0.0)
    
    # Revisão
    reviewed_by = Column(String(255), nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    project = relationship("CarbonProject", back_populates="fraud_alerts")


# ─── Módulo 3: Dashboard de Portfólio ───────────────────────────────────

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    description = Column(Text, nullable=True)
    
    # Métricas calculadas
    total_credits = Column(Integer, default=0)
    total_value_usd = Column(Float, default=0)
    avg_quality_score = Column(Float, default=0)
    risk_exposure = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    organization = relationship("Organization", back_populates="portfolios")
    positions = relationship("PortfolioPosition", back_populates="portfolio")


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    credit_id = Column(Integer, ForeignKey("carbon_credits.id"), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    acquisition_price_usd = Column(Float, nullable=True)
    acquisition_date = Column(DateTime, nullable=True)
    planned_retirement_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=utcnow)

    portfolio = relationship("Portfolio", back_populates="positions")
    credit = relationship("CarbonCredit", back_populates="positions")
