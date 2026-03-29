"""Endpoints de Projetos de Carbono e Ratings."""
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import CarbonProject, ProjectRating, FraudAlert, CarbonCredit, User
from app.models.schemas import (
    ProjectCreate, ProjectResponse, ProjectWithRating, RatingResponse
)
from app.services.rating_engine import calculate_rating
from app.services.fraud_detection import run_fraud_detection

router = APIRouter(prefix="/projects", tags=["Projetos de Carbono"])

PAGE_SIZE = 20


def _serialize_project(project, rating=None, alert_count=0):
    """Serializa um projeto com rating e contagem de alertas."""
    proj_dict = {
        "id": project.id,
        "external_id": project.external_id,
        "name": project.name,
        "description": project.description,
        "project_type": project.project_type.value if hasattr(project.project_type, 'value') else str(project.project_type),
        "methodology": project.methodology,
        "registry": project.registry,
        "country": project.country,
        "region": project.region,
        "latitude": project.latitude,
        "longitude": project.longitude,
        "proponent": project.proponent,
        "total_credits_issued": project.total_credits_issued,
        "total_credits_retired": project.total_credits_retired,
        "total_credits_available": project.total_credits_available,
        "vintage_year": project.vintage_year,
        "area_hectares": project.area_hectares,
        "created_at": project.created_at,
        "rating": None,
        "fraud_alert_count": alert_count,
    }

    if rating:
        proj_dict["rating"] = {
            "id": rating.id,
            "project_id": rating.project_id,
            "overall_score": rating.overall_score,
            "grade": rating.grade.value if hasattr(rating.grade, 'value') else str(rating.grade),
            "additionality_score": rating.additionality_score,
            "permanence_score": rating.permanence_score,
            "leakage_score": rating.leakage_score,
            "mrv_score": rating.mrv_score,
            "co_benefits_score": rating.co_benefits_score,
            "governance_score": rating.governance_score,
            "baseline_integrity_score": rating.baseline_integrity_score,
            "confidence_level": rating.confidence_level,
            "explanation": rating.explanation,
            "risk_flags": rating.risk_flags,
            "rated_at": rating.rated_at,
        }

    return proj_dict


@router.get("")
async def list_projects(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(PAGE_SIZE, ge=1, le=100, description="Itens por página"),
    project_type: Optional[str] = None,
    country: Optional[str] = None,
    registry: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Lista projetos de carbono com filtros, ratings e paginação."""
    # Base query para contagem e dados
    base_query = select(CarbonProject)

    if project_type:
        base_query = base_query.where(CarbonProject.project_type == project_type)
    if country:
        base_query = base_query.where(CarbonProject.country == country)
    if registry:
        base_query = base_query.where(CarbonProject.registry == registry)
    if search:
        base_query = base_query.where(CarbonProject.name.ilike(f"%{search}%"))

    # Filtros por score requerem join com rating
    if min_score is not None or max_score is not None:
        base_query = base_query.join(ProjectRating, CarbonProject.id == ProjectRating.project_id)
        if min_score is not None:
            base_query = base_query.where(ProjectRating.overall_score >= min_score)
        if max_score is not None:
            base_query = base_query.where(ProjectRating.overall_score <= max_score)

    # Contagem total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    # Query paginada com eager loading
    offset = (page - 1) * page_size
    data_query = (
        base_query
        .options(selectinload(CarbonProject.rating))
        .options(selectinload(CarbonProject.fraud_alerts))
        .order_by(CarbonProject.id)
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(data_query)
    projects = result.scalars().unique().all()

    items = []
    for project in projects:
        rating = project.rating
        alert_count = len(project.fraud_alerts) if project.fraud_alerts else 0
        items.append(_serialize_project(project, rating, alert_count))

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{project_id}")
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """Retorna detalhes de um projeto com rating e contagem de alertas."""
    result = await db.execute(
        select(CarbonProject)
        .options(selectinload(CarbonProject.rating))
        .options(selectinload(CarbonProject.fraud_alerts))
        .where(CarbonProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    rating = project.rating
    alert_count = len(project.fraud_alerts) if project.fraud_alerts else 0
    return _serialize_project(project, rating, alert_count)


@router.post("", status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria um novo projeto e calcula rating automaticamente."""
    project = CarbonProject(**data.model_dump())
    db.add(project)
    await db.flush()

    # Calcular rating
    rating = calculate_rating(project)
    db.add(rating)

    # Executar fraud detection
    alerts = run_fraud_detection(project)
    for alert in alerts:
        db.add(alert)

    await db.commit()
    await db.refresh(project)
    await db.refresh(rating)

    return {
        "id": project.id,
        "name": project.name,
        "project_type": project.project_type.value if hasattr(project.project_type, 'value') else str(project.project_type),
        "rating": {
            "overall_score": rating.overall_score,
            "grade": rating.grade.value if hasattr(rating.grade, 'value') else str(rating.grade),
        },
        "fraud_alert_count": len(alerts),
    }


@router.post("/{project_id}/recalculate-rating")
async def recalculate_rating(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recalcula o rating de um projeto."""
    result = await db.execute(select(CarbonProject).where(CarbonProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    old_rating = await db.execute(
        select(ProjectRating).where(ProjectRating.project_id == project_id)
    )
    old = old_rating.scalar_one_or_none()
    if old:
        await db.delete(old)

    rating = calculate_rating(project)
    db.add(rating)
    await db.commit()
    await db.refresh(rating)

    return {
        "id": rating.id,
        "project_id": rating.project_id,
        "overall_score": rating.overall_score,
        "grade": rating.grade.value if hasattr(rating.grade, 'value') else str(rating.grade),
        "additionality_score": rating.additionality_score,
        "permanence_score": rating.permanence_score,
        "leakage_score": rating.leakage_score,
        "mrv_score": rating.mrv_score,
        "co_benefits_score": rating.co_benefits_score,
        "governance_score": rating.governance_score,
        "baseline_integrity_score": rating.baseline_integrity_score,
        "confidence_level": rating.confidence_level,
        "explanation": rating.explanation,
        "risk_flags": rating.risk_flags,
    }


@router.get("/{project_id}/rating")
async def get_project_rating(project_id: int, db: AsyncSession = Depends(get_db)):
    """Retorna o rating detalhado de um projeto."""
    result = await db.execute(
        select(ProjectRating).where(ProjectRating.project_id == project_id)
    )
    rating = result.scalar_one_or_none()
    if not rating:
        raise HTTPException(status_code=404, detail="Rating não encontrado para este projeto")

    return {
        "id": rating.id,
        "project_id": rating.project_id,
        "overall_score": rating.overall_score,
        "grade": rating.grade.value if hasattr(rating.grade, 'value') else str(rating.grade),
        "additionality_score": rating.additionality_score,
        "permanence_score": rating.permanence_score,
        "leakage_score": rating.leakage_score,
        "mrv_score": rating.mrv_score,
        "co_benefits_score": rating.co_benefits_score,
        "governance_score": rating.governance_score,
        "baseline_integrity_score": rating.baseline_integrity_score,
        "confidence_level": rating.confidence_level,
        "explanation": rating.explanation,
        "risk_flags": rating.risk_flags,
        "rated_at": str(rating.rated_at) if rating.rated_at else None,
    }
