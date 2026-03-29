"""Endpoints de Fraud Detection."""
import math
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import FraudAlert, CarbonProject, User, AlertStatus
from app.models.schemas import FraudAlertResponse, FraudAlertUpdate

router = APIRouter(prefix="/fraud-alerts", tags=["Fraud Detection"])

PAGE_SIZE = 20


@router.get("")
async def list_fraud_alerts(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(PAGE_SIZE, ge=1, le=100, description="Itens por página"),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    project_id: Optional[int] = None,
    alert_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Lista alertas de fraude com filtros e paginação."""
    base_query = select(FraudAlert)

    if severity:
        base_query = base_query.where(FraudAlert.severity == severity)
    if status:
        base_query = base_query.where(FraudAlert.status == status)
    if project_id:
        base_query = base_query.where(FraudAlert.project_id == project_id)
    if alert_type:
        base_query = base_query.where(FraudAlert.alert_type == alert_type)

    # Contagem total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    # Query paginada
    offset = (page - 1) * page_size
    data_query = base_query.order_by(FraudAlert.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(data_query)
    alerts = result.scalars().all()

    return {
        "items": [FraudAlertResponse.model_validate(a) for a in alerts],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/summary")
async def fraud_summary(db: AsyncSession = Depends(get_db)):
    """Retorna resumo dos alertas de fraude."""
    # Total por severidade
    severity_result = await db.execute(
        select(FraudAlert.severity, func.count(FraudAlert.id))
        .group_by(FraudAlert.severity)
    )
    by_severity = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in severity_result.all()}

    # Total por status
    status_result = await db.execute(
        select(FraudAlert.status, func.count(FraudAlert.id))
        .group_by(FraudAlert.status)
    )
    by_status = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in status_result.all()}

    # Total por tipo
    type_result = await db.execute(
        select(FraudAlert.alert_type, func.count(FraudAlert.id))
        .group_by(FraudAlert.alert_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}

    # Projetos mais afetados
    top_projects = await db.execute(
        select(FraudAlert.project_id, CarbonProject.name, func.count(FraudAlert.id).label("alert_count"))
        .join(CarbonProject, FraudAlert.project_id == CarbonProject.id)
        .group_by(FraudAlert.project_id, CarbonProject.name)
        .order_by(func.count(FraudAlert.id).desc())
        .limit(5)
    )

    return {
        "total_alerts": sum(by_severity.values()),
        "by_severity": by_severity,
        "by_status": by_status,
        "by_type": by_type,
        "top_affected_projects": [
            {"project_id": row[0], "project_name": row[1], "alert_count": row[2]}
            for row in top_projects.all()
        ],
    }


@router.get("/{alert_id}", response_model=FraudAlertResponse)
async def get_fraud_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """Retorna detalhes de um alerta de fraude."""
    result = await db.execute(select(FraudAlert).where(FraudAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    return FraudAlertResponse.model_validate(alert)


@router.patch("/{alert_id}", response_model=FraudAlertResponse)
async def update_fraud_alert(
    alert_id: int,
    data: FraudAlertUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualiza status/revisão de um alerta de fraude."""
    result = await db.execute(select(FraudAlert).where(FraudAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")

    if data.status:
        alert.status = data.status
    if data.review_notes:
        alert.review_notes = data.review_notes
    if data.reviewed_by:
        alert.reviewed_by = data.reviewed_by

    alert.reviewed_at = datetime.now(timezone.utc)
    alert.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(alert)

    return FraudAlertResponse.model_validate(alert)
