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

# ─── Explicacoes detalhadas para leigos sobre cada tipo de fraude ─────────

FRAUD_TYPE_EXPLANATIONS = {
    "overcrediting": {
        "title": "Overcrediting (Creditos em Excesso)",
        "what_is": (
            "Overcrediting ocorre quando um projeto de carbono emite mais creditos do que a quantidade real "
            "de carbono que foi efetivamente removida ou evitada. Em termos simples, e como se o projeto "
            "\"inflasse\" seus numeros, declarando ter compensado mais emissoes do que realmente compensou."
        ),
        "consequences": (
            "Quando creditos em excesso sao vendidos no mercado, compradores acreditam estar compensando "
            "suas emissoes, mas na realidade a compensacao nao aconteceu integralmente. Isso mina a "
            "credibilidade do mercado de carbono, contribui para o greenwashing corporativo e, em ultima "
            "instancia, significa que mais CO2 permanece na atmosfera do que o declarado."
        ),
        "ideal_situation": (
            "O ideal e que o projeto utilize metodologias conservadoras de calculo, com verificacao "
            "independente por terceiros credenciados. A quantidade de creditos emitidos deve ser igual "
            "ou inferior a quantidade real de carbono sequestrado/evitado, com margem de seguranca "
            "(buffer) aplicada. Auditorias regulares devem confirmar os numeros."
        ),
        "icon": "alert-triangle",
        "severity_typical": "high",
    },
    "vintage_age": {
        "title": "Vintage Antigo (Creditos Envelhecidos)",
        "what_is": (
            "Vintage age refere-se a creditos de carbono que foram gerados ha muitos anos (tipicamente "
            "mais de 5 anos) e ainda nao foram aposentados (utilizados). Creditos muito antigos podem "
            "nao refletir as condicoes atuais do projeto ou as metodologias mais recentes de calculo."
        ),
        "consequences": (
            "Creditos antigos podem representar reducoes de emissoes que ja nao sao adicionais (ou seja, "
            "teriam acontecido de qualquer forma). O projeto pode ter mudado, sido abandonado ou degradado "
            "desde a emissao dos creditos. Compradores podem estar pagando por beneficios climaticos que "
            "ja nao existem na pratica."
        ),
        "ideal_situation": (
            "O ideal e que creditos sejam utilizados dentro de 3-5 anos apos sua emissao. Projetos devem "
            "manter monitoramento continuo e os creditos devem refletir reducoes de emissoes recentes e "
            "verificaveis. Registros devem aplicar politicas de expiracao ou desconto para vintages antigos."
        ),
        "icon": "clock",
        "severity_typical": "medium",
    },
    "retirement_anomaly": {
        "title": "Anomalia de Aposentadoria",
        "what_is": (
            "Uma anomalia de aposentadoria ocorre quando o padrao de aposentadoria (uso) dos creditos "
            "de carbono apresenta comportamento incomum - por exemplo, um volume muito grande de creditos "
            "aposentados de uma so vez, aposentadorias em datas suspeitas, ou padroes que sugerem "
            "manipulacao contabil."
        ),
        "consequences": (
            "Padroes anomalos podem indicar tentativas de manipulacao do mercado, dupla contagem "
            "(o mesmo credito sendo \"usado\" mais de uma vez em diferentes jurisdicoes), ou fraude "
            "direta. Isso compromete a integridade do sistema de rastreamento e pode resultar em "
            "compensacoes ficticias."
        ),
        "ideal_situation": (
            "O ideal e que aposentadorias sigam um padrao regular e proporcional ao tamanho do projeto. "
            "Cada credito deve ter um identificador unico e ser aposentado apenas uma vez, com registro "
            "publico e transparente. Sistemas de registro devem implementar verificacoes automaticas "
            "contra dupla contagem."
        ),
        "icon": "repeat",
        "severity_typical": "high",
    },
    "missing_area": {
        "title": "Area do Projeto Ausente ou Inconsistente",
        "what_is": (
            "Este alerta indica que o projeto nao possui informacoes geograficas adequadas sobre sua "
            "area de atuacao, ou que a area declarada e inconsistente com imagens de satelite e dados "
            "geoespaciais. Em termos simples, nao se sabe exatamente onde o projeto esta ou se a area "
            "declarada corresponde a realidade."
        ),
        "consequences": (
            "Sem dados geograficos confiaveis, e impossivel verificar se o projeto realmente existe "
            "fisicamente, se a floresta declarada esta de pe, ou se a area nao se sobrepoe a outros "
            "projetos. Projetos fantasma (que existem apenas no papel) sao uma das formas mais graves "
            "de fraude no mercado de carbono."
        ),
        "ideal_situation": (
            "O ideal e que todo projeto tenha coordenadas geograficas precisas (shapefiles/KML), "
            "com verificacao por imagens de satelite atualizadas. A area deve ser validada por "
            "auditores independentes e nao deve haver sobreposicao com outros projetos registrados. "
            "Monitoramento remoto continuo deve confirmar a integridade da area."
        ),
        "icon": "map-pin",
        "severity_typical": "medium",
    },
    "governance_gaps": {
        "title": "Lacunas de Governanca",
        "what_is": (
            "Lacunas de governanca referem-se a ausencia de informacoes essenciais sobre a gestao, "
            "transparencia e conformidade do projeto. Isso inclui falta de documentacao sobre o "
            "desenvolvedor do projeto, ausencia de relatorios de monitoramento, falta de validacao "
            "por terceiros, ou informacoes incompletas sobre stakeholders e comunidades afetadas."
        ),
        "consequences": (
            "Projetos com governanca fraca sao mais suscetiveis a fraudes, conflitos com comunidades "
            "locais, violacoes de direitos humanos e falhas operacionais. A falta de transparencia "
            "impede que investidores e compradores avaliem adequadamente os riscos. Em casos extremos, "
            "projetos podem estar associados a grilagem de terras ou deslocamento de comunidades."
        ),
        "ideal_situation": (
            "O ideal e que o projeto tenha documentacao completa e publica: relatorio de validacao, "
            "relatorios de monitoramento periodicos, informacoes sobre o desenvolvedor e sua "
            "reputacao, consentimento livre e informado das comunidades locais (FPIC), mecanismo "
            "de reclamacoes acessivel, e auditorias regulares por verificadores credenciados."
        ),
        "icon": "file-warning",
        "severity_typical": "medium",
    },
    "insufficient_buffer": {
        "title": "Buffer de Permanencia Insuficiente",
        "what_is": (
            "O buffer de permanencia e uma reserva de creditos que o projeto mantem como \"seguro\" "
            "contra riscos de reversao (por exemplo, uma floresta que queima ou e desmatada apos "
            "receber creditos). Quando o buffer e insuficiente, significa que o projeto nao tem "
            "protecao adequada contra a perda do carbono que declarou ter sequestrado."
        ),
        "consequences": (
            "Se ocorrer uma reversao (incendio, praga, desmatamento ilegal) e o buffer for "
            "insuficiente, os creditos ja vendidos nao poderao ser compensados. Isso significa que "
            "compradores pagaram por reducoes de emissoes que foram revertidas, resultando em um "
            "impacto climatico liquido zero ou negativo. O risco e especialmente alto em projetos "
            "florestais de longo prazo."
        ),
        "ideal_situation": (
            "O ideal e que projetos florestais mantenham um buffer minimo de 15-20% dos creditos "
            "emitidos, ajustado conforme o perfil de risco (localizacao, tipo de floresta, riscos "
            "politicos). O buffer deve ser gerido por um pool coletivo no registro para diversificar "
            "o risco. Monitoramento continuo deve detectar reversoes precocemente."
        ),
        "icon": "shield-off",
        "severity_typical": "high",
    },
}


def _alert_to_response_with_name(alert, project_name: str) -> dict:
    """Converte um alerta para dict de resposta incluindo project_name."""
    data = FraudAlertResponse.model_validate(alert).model_dump()
    data["project_name"] = project_name
    return data


@router.get("")
async def list_fraud_alerts(
    page: int = Query(1, ge=1, description="Numero da pagina"),
    page_size: int = Query(PAGE_SIZE, ge=1, le=100, description="Itens por pagina"),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    project_id: Optional[int] = None,
    alert_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Lista alertas de fraude com filtros e paginacao."""
    base_query = (
        select(FraudAlert, CarbonProject.name.label("project_name"))
        .join(CarbonProject, FraudAlert.project_id == CarbonProject.id)
    )

    if severity:
        base_query = base_query.where(FraudAlert.severity == severity)
    if status:
        base_query = base_query.where(FraudAlert.status == status)
    if project_id:
        base_query = base_query.where(FraudAlert.project_id == project_id)
    if alert_type:
        base_query = base_query.where(FraudAlert.alert_type == alert_type)

    # Contagem total
    count_base = select(FraudAlert.id)
    if severity:
        count_base = count_base.where(FraudAlert.severity == severity)
    if status:
        count_base = count_base.where(FraudAlert.status == status)
    if project_id:
        count_base = count_base.where(FraudAlert.project_id == project_id)
    if alert_type:
        count_base = count_base.where(FraudAlert.alert_type == alert_type)
    count_query = select(func.count()).select_from(count_base.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    # Query paginada
    offset = (page - 1) * page_size
    data_query = base_query.order_by(FraudAlert.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(data_query)
    rows = result.all()

    items = []
    for row in rows:
        alert = row[0]
        project_name = row[1]
        items.append(_alert_to_response_with_name(alert, project_name))

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/grouped-by-type")
async def fraud_alerts_grouped_by_type(
    page_size: int = Query(10, ge=1, le=50, description="Alertas por pagina por aba"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna alertas de fraude agrupados por tipo, com paginacao independente
    por aba e explicacoes detalhadas para cada tipo de fraude.
    """
    # Obter todos os tipos de alerta existentes
    type_result = await db.execute(
        select(FraudAlert.alert_type, func.count(FraudAlert.id))
        .group_by(FraudAlert.alert_type)
        .order_by(func.count(FraudAlert.id).desc())
    )
    type_counts = {row[0]: row[1] for row in type_result.all()}

    grouped = {}
    for alert_type, total_count in type_counts.items():
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        # Buscar alertas deste tipo com project_name (primeira pagina)
        alerts_result = await db.execute(
            select(FraudAlert, CarbonProject.name.label("project_name"))
            .join(CarbonProject, FraudAlert.project_id == CarbonProject.id)
            .where(FraudAlert.alert_type == alert_type)
            .order_by(FraudAlert.severity.desc(), FraudAlert.created_at.desc())
            .offset(0)
            .limit(page_size)
        )
        rows = alerts_result.all()

        items = []
        for row in rows:
            alert = row[0]
            project_name = row[1]
            items.append(_alert_to_response_with_name(alert, project_name))

        # Obter explicacao do tipo
        explanation = FRAUD_TYPE_EXPLANATIONS.get(alert_type, {
            "title": alert_type.replace("_", " ").title(),
            "what_is": "Tipo de alerta sem descricao detalhada disponivel.",
            "consequences": "Consequencias nao documentadas para este tipo.",
            "ideal_situation": "Situacao ideal nao documentada para este tipo.",
            "icon": "alert-circle",
            "severity_typical": "medium",
        })

        grouped[alert_type] = {
            "items": items,
            "total": total_count,
            "page": 1,
            "page_size": page_size,
            "total_pages": total_pages,
            "explanation": explanation,
        }

    return {
        "types": grouped,
        "total_types": len(type_counts),
        "total_alerts": sum(type_counts.values()),
    }


@router.get("/grouped-by-type/{alert_type}")
async def fraud_alerts_by_type_paginated(
    alert_type: str,
    page: int = Query(1, ge=1, description="Numero da pagina"),
    page_size: int = Query(10, ge=1, le=50, description="Alertas por pagina"),
    db: AsyncSession = Depends(get_db),
):
    """Retorna alertas de um tipo especifico com paginacao."""
    # Contagem
    count_query = select(func.count()).select_from(
        select(FraudAlert.id).where(FraudAlert.alert_type == alert_type).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size

    # Buscar alertas com project_name
    data_query = (
        select(FraudAlert, CarbonProject.name.label("project_name"))
        .join(CarbonProject, FraudAlert.project_id == CarbonProject.id)
        .where(FraudAlert.alert_type == alert_type)
        .order_by(FraudAlert.severity.desc(), FraudAlert.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(data_query)
    rows = result.all()

    items = []
    for row in rows:
        alert = row[0]
        project_name = row[1]
        items.append(_alert_to_response_with_name(alert, project_name))

    explanation = FRAUD_TYPE_EXPLANATIONS.get(alert_type, {
        "title": alert_type.replace("_", " ").title(),
        "what_is": "Tipo de alerta sem descricao detalhada disponivel.",
        "consequences": "Consequencias nao documentadas para este tipo.",
        "ideal_situation": "Situacao ideal nao documentada para este tipo.",
        "icon": "alert-circle",
        "severity_typical": "medium",
    })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "explanation": explanation,
    }


@router.get("/summary")
async def fraud_summary(db: AsyncSession = Depends(get_db)):
    """Retorna resumo dos alertas de fraude."""
    severity_result = await db.execute(
        select(FraudAlert.severity, func.count(FraudAlert.id))
        .group_by(FraudAlert.severity)
    )
    by_severity = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in severity_result.all()}

    status_result = await db.execute(
        select(FraudAlert.status, func.count(FraudAlert.id))
        .group_by(FraudAlert.status)
    )
    by_status = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in status_result.all()}

    type_result = await db.execute(
        select(FraudAlert.alert_type, func.count(FraudAlert.id))
        .group_by(FraudAlert.alert_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}

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


@router.get("/{alert_id}")
async def get_fraud_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """Retorna detalhes de um alerta de fraude."""
    result = await db.execute(
        select(FraudAlert, CarbonProject.name.label("project_name"))
        .join(CarbonProject, FraudAlert.project_id == CarbonProject.id)
        .where(FraudAlert.id == alert_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Alerta nao encontrado")
    alert = row[0]
    project_name = row[1]
    return _alert_to_response_with_name(alert, project_name)


@router.patch("/{alert_id}")
async def update_fraud_alert(
    alert_id: int,
    data: FraudAlertUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualiza status de um alerta de fraude."""
    result = await db.execute(select(FraudAlert).where(FraudAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta nao encontrado")

    if data.status:
        alert.status = data.status
    if data.review_notes:
        alert.review_notes = data.review_notes
    if data.reviewed_by:
        alert.reviewed_by = data.reviewed_by
    alert.reviewed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(alert)

    # Buscar project_name
    proj_result = await db.execute(
        select(CarbonProject.name).where(CarbonProject.id == alert.project_id)
    )
    project_name = proj_result.scalar() or "N/A"
    return _alert_to_response_with_name(alert, project_name)
