"""Endpoints de Portfólio e Dashboard."""
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import (
    Portfolio, PortfolioPosition, CarbonCredit, CarbonProject,
    User, ProjectRating, FraudAlert
)
from app.models.schemas import (
    PortfolioCreate, PortfolioResponse, PositionCreate, PositionResponse,
    DashboardMetrics
)
from app.services.portfolio_analytics import calculate_portfolio_metrics, get_dashboard_metrics, group_recommendations_by_action

router = APIRouter(prefix="/portfolios", tags=["Portfólios"])

PAGE_SIZE = 20


@router.get("", response_model=list[PortfolioResponse])
async def list_portfolios(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista portfólios da organização do usuário."""
    result = await db.execute(
        select(Portfolio).where(Portfolio.organization_id == current_user.organization_id)
    )
    portfolios = result.scalars().all()
    return [PortfolioResponse.model_validate(p) for p in portfolios]


@router.post("", response_model=PortfolioResponse, status_code=201)
async def create_portfolio(
    data: PortfolioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria um novo portfólio."""
    portfolio = Portfolio(
        name=data.name,
        description=data.description,
        organization_id=current_user.organization_id,
    )
    db.add(portfolio)
    await db.commit()
    await db.refresh(portfolio)
    return PortfolioResponse.model_validate(portfolio)


@router.get("/{portfolio_id}")
async def get_portfolio_detail(
    portfolio_id: int,
    page: int = Query(1, ge=1, description="Página das posições"),
    page_size: int = Query(PAGE_SIZE, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna detalhes do portfólio com métricas, recomendações e posições paginadas."""
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfólio não encontrado")
    if portfolio.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    metrics = await calculate_portfolio_metrics(db, portfolio_id)

    # Paginar posições
    all_positions = metrics.get("positions", [])
    total_positions = len(all_positions)
    total_pages = math.ceil(total_positions / page_size) if total_positions > 0 else 1
    offset = (page - 1) * page_size
    paginated_positions = all_positions[offset:offset + page_size]

    metrics["positions"] = paginated_positions
    metrics["positions_pagination"] = {
        "total": total_positions,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }

    # Agrupar recomendações por ação para exibição em abas
    recommendations = metrics.get("recommendations", [])
    metrics["recommendations_grouped"] = group_recommendations_by_action(recommendations)

    return {
        "portfolio": PortfolioResponse.model_validate(portfolio),
        "metrics": metrics,
    }


@router.post("/{portfolio_id}/positions", response_model=PositionResponse, status_code=201)
async def add_position(
    portfolio_id: int,
    data: PositionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Adiciona uma posição ao portfólio."""
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfólio não encontrado")
    if portfolio.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    credit_result = await db.execute(select(CarbonCredit).where(CarbonCredit.id == data.credit_id))
    if not credit_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Crédito não encontrado")

    position = PortfolioPosition(
        portfolio_id=portfolio_id,
        **data.model_dump(),
    )
    db.add(position)

    portfolio.total_credits += data.quantity
    if data.acquisition_price_usd:
        portfolio.total_value_usd += data.quantity * data.acquisition_price_usd

    await db.commit()
    await db.refresh(position)
    return PositionResponse.model_validate(position)


# ─── Dashboard ───────────────────────────────────────────────────────────

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@dashboard_router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna métricas agregadas para o dashboard principal."""
    metrics = await get_dashboard_metrics(db, current_user.organization_id)
    return DashboardMetrics(**metrics)


@dashboard_router.get("/risk-matrix")
async def get_risk_matrix(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna dados para a matriz de risco do dashboard."""
    result = await db.execute(
        select(
            CarbonProject.id,
            CarbonProject.name,
            CarbonProject.project_type,
            ProjectRating.overall_score,
            ProjectRating.grade,
            func.count(FraudAlert.id).label("fraud_count"),
        )
        .outerjoin(ProjectRating, CarbonProject.id == ProjectRating.project_id)
        .outerjoin(FraudAlert, CarbonProject.id == FraudAlert.project_id)
        .group_by(
            CarbonProject.id,
            CarbonProject.name,
            CarbonProject.project_type,
            ProjectRating.overall_score,
            ProjectRating.grade,
        )
    )

    return [
        {
            "project_id": row[0],
            "name": row[1],
            "project_type": row[2].value if hasattr(row[2], 'value') else str(row[2]) if row[2] else "N/A",
            "quality_score": row[3] or 0,
            "grade": row[4].value if hasattr(row[4], 'value') else str(row[4]) if row[4] else "N/A",
            "fraud_alerts": row[5],
        }
        for row in result.all()
    ]
