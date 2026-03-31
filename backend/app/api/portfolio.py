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
    rec_page: int = Query(1, ge=1, description="Página das recomendações (dentro de cada aba)"),
    rec_page_size: int = Query(PAGE_SIZE, ge=1, le=100, description="Recomendações por página por aba"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna detalhes do portfólio com métricas, recomendações paginadas e posições paginadas."""
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

    # Agrupar recomendações por ação com paginação por aba
    recommendations = metrics.get("recommendations", [])
    metrics["recommendations_grouped"] = group_recommendations_by_action(
        recommendations, page=rec_page, page_size=rec_page_size
    )

    # Contagem total de recomendações (sem duplicação)
    metrics["total_recommendations"] = len(recommendations)

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
    if data.acquisition_price_eur:
        portfolio.total_value_eur += data.quantity * data.acquisition_price_eur

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
    """Retorna dados para a matriz de risco em formato de tabela quadriculada.
    
    Eixo Y (linhas): Nível de Qualidade (score) - Alto (>60), Médio (40-60), Baixo (<40)
    Eixo X (colunas): Nível de Risco (fraud alerts) - Sem Alertas, Baixo (1-2), Médio (3-4), Alto (5+)
    Cada célula contém a lista de projetos e a contagem.
    """
    result = await db.execute(
        select(
            CarbonProject.id,
            CarbonProject.name,
            CarbonProject.project_type,
            CarbonProject.registry,
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
            CarbonProject.registry,
            ProjectRating.overall_score,
            ProjectRating.grade,
        )
    )

    projects = []
    for row in result.all():
        projects.append({
            "project_id": row[0],
            "name": row[1],
            "project_type": row[2].value if hasattr(row[2], 'value') else str(row[2]) if row[2] else "N/A",
            "registry": row[3].value if hasattr(row[3], 'value') else str(row[3]) if row[3] else "N/A",
            "quality_score": row[4] or 0,
            "grade": row[5].value if hasattr(row[5], 'value') else str(row[5]) if row[5] else "N/A",
            "fraud_alerts": row[6],
        })

    # Definir categorias
    quality_levels = [
        {"key": "high", "label": "Alta Qualidade (Score > 60)", "min": 60.01, "max": 100},
        {"key": "medium", "label": "Qualidade Média (Score 40-60)", "min": 40, "max": 60},
        {"key": "low", "label": "Baixa Qualidade (Score < 40)", "min": 0, "max": 39.99},
    ]
    risk_levels = [
        {"key": "none", "label": "Sem Alertas", "min": 0, "max": 0},
        {"key": "low", "label": "Baixo (1-2)", "min": 1, "max": 2},
        {"key": "medium", "label": "Médio (3-4)", "min": 3, "max": 4},
        {"key": "high", "label": "Alto (5+)", "min": 5, "max": 999},
    ]

    def classify_quality(score):
        if score > 60:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"

    def classify_risk(fraud_count):
        if fraud_count == 0:
            return "none"
        elif fraud_count <= 2:
            return "low"
        elif fraud_count <= 4:
            return "medium"
        else:
            return "high"

    # Construir grid
    grid = {}
    for ql in quality_levels:
        grid[ql["key"]] = {}
        for rl in risk_levels:
            grid[ql["key"]][rl["key"]] = {
                "projects": [],
                "count": 0,
            }

    for p in projects:
        q_key = classify_quality(p["quality_score"])
        r_key = classify_risk(p["fraud_alerts"])
        cell = grid[q_key][r_key]
        cell["projects"].append(p)
        cell["count"] += 1

    return {
        "grid": grid,
        "quality_levels": quality_levels,
        "risk_levels": risk_levels,
        "total_projects": len(projects),
        "projects": projects,
    }
