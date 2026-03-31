"""
Serviço de Analytics de Portfólio - Carbon Verify

Implementa cálculos de métricas de risco, qualidade e
recomendações de rebalanceamento conforme Módulo 3.

Correções v5:
  - Deduplicação: posições do mesmo projeto são agregadas antes de gerar recomendações
  - Flags de risco: cada recomendação inclui risk_flags detalhados do rating
  - Motivos: cada recomendação inclui reasons (lista de motivos) além do reason principal
  - Paginação: recomendações agrupadas por ação suportam paginação server-side
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from app.models.models import (
    Portfolio, PortfolioPosition, CarbonCredit, CarbonProject,
    ProjectRating, FraudAlert, RatingGrade
)


async def calculate_portfolio_metrics(db: AsyncSession, portfolio_id: int) -> dict:
    """Calcula métricas agregadas do portfólio."""
    result = await db.execute(
        select(PortfolioPosition, CarbonCredit, CarbonProject, ProjectRating)
        .join(CarbonCredit, PortfolioPosition.credit_id == CarbonCredit.id)
        .join(CarbonProject, CarbonCredit.project_id == CarbonProject.id)
        .outerjoin(ProjectRating, CarbonProject.id == ProjectRating.project_id)
        .where(PortfolioPosition.portfolio_id == portfolio_id)
    )
    rows = result.all()

    if not rows:
        return {
            "total_credits": 0,
            "total_value_eur": 0,
            "avg_quality_score": 0,
            "grade_distribution": {},
            "risk_exposure": {},
            "project_type_distribution": {},
            "country_distribution": {},
            "recommendations": [],
            "positions": [],
        }

    total_credits = 0
    total_value = 0
    weighted_score_sum = 0
    grade_dist = {}
    type_dist = {}
    country_dist = {}
    risk_exposure = {"high": 0, "medium": 0, "low": 0}

    # ─── Agregar posições por projeto (deduplicação) ───────────────
    project_agg = {}  # project_id -> aggregated data
    position_list = []  # flat list for positions table (still per-position)

    for position, credit, project, rating in rows:
        qty = position.quantity
        total_credits += qty

        price = position.acquisition_price_eur or credit.price_eur or 0
        total_value += qty * price

        score = rating.overall_score if rating else 50
        grade = rating.grade.value if rating else "N/A"
        risk_flags = rating.risk_flags if rating and rating.risk_flags else []
        weighted_score_sum += score * qty

        # Distribuição de grades
        grade_dist[grade] = grade_dist.get(grade, 0) + qty

        # Distribuição por tipo
        ptype = project.project_type if isinstance(project.project_type, str) else project.project_type.value
        type_dist[ptype] = type_dist.get(ptype, 0) + qty

        # Distribuição por país
        country_dist[project.country] = country_dist.get(project.country, 0) + qty

        # Exposição a risco
        if score < 40:
            risk_exposure["high"] += qty
        elif score < 60:
            risk_exposure["medium"] += qty
        else:
            risk_exposure["low"] += qty

        # Agregar por projeto (para recomendações sem duplicação)
        pid = project.id
        if pid not in project_agg:
            project_agg[pid] = {
                "project_id": pid,
                "project_name": project.name,
                "project_type": ptype,
                "country": project.country,
                "registry": project.registry,
                "total_quantity": 0,
                "total_value": 0,
                "score": score,
                "grade": grade,
                "risk_flags": risk_flags,
                "num_positions": 0,
                "avg_price_eur": 0,
            }
        project_agg[pid]["total_quantity"] += qty
        project_agg[pid]["total_value"] += qty * price
        project_agg[pid]["num_positions"] += 1

        # Lista de posições (para tabela detalhada)
        position_list.append({
            "position_id": position.id,
            "project_id": project.id,
            "project_name": project.name,
            "project_type": ptype,
            "country": project.country,
            "quantity": qty,
            "score": score,
            "grade": grade,
            "price_eur": price,
        })

    # Calcular preço médio por projeto
    for pid in project_agg:
        agg = project_agg[pid]
        agg["avg_price_eur"] = round(agg["total_value"] / agg["total_quantity"], 2) if agg["total_quantity"] > 0 else 0

    avg_score = weighted_score_sum / total_credits if total_credits > 0 else 0

    # Gerar recomendações DEDUPLICADAS (1 por projeto, não por posição)
    project_details = list(project_agg.values())
    recommendations = _generate_recommendations(project_details, avg_score, type_dist, country_dist)

    return {
        "total_credits": total_credits,
        "total_value_eur": round(total_value, 2),
        "avg_quality_score": round(avg_score, 2),
        "grade_distribution": grade_dist,
        "risk_exposure": risk_exposure,
        "project_type_distribution": type_dist,
        "country_distribution": country_dist,
        "recommendations": recommendations,
        "positions": position_list,
    }


def _generate_risk_flag_summary(risk_flags: list) -> list:
    """Gera resumo de flags de risco para exibição na recomendação."""
    if not risk_flags:
        return []
    summary = []
    for flag in risk_flags:
        summary.append({
            "type": flag.get("type", "unknown"),
            "severity": flag.get("severity", "medium"),
            "message": flag.get("message", ""),
        })
    return summary


def _generate_reasons(project: dict, action: str, avg_score: float) -> list:
    """Gera lista detalhada de motivos para a recomendação."""
    reasons = []
    score = project["score"]
    grade = project["grade"]
    risk_flags = project.get("risk_flags", [])

    if action == "sell":
        reasons.append(f"Score de qualidade muito baixo: {score:.0f}/100 (grade {grade})")
        if score < 25:
            reasons.append("Score crítico abaixo de 25 - alto risco de perda total de valor")
        if project.get("registry") and project.get("total_quantity", 0) > 10000:
            reasons.append(f"Exposição significativa: {project['total_quantity']:,} créditos em risco")
        for flag in risk_flags:
            if flag.get("severity") == "high":
                reasons.append(f"Flag de risco alto: {flag.get('message', 'N/A')}")
        if not reasons or len(reasons) < 2:
            reasons.append("Documentação insuficiente para verificação adequada")

    elif action == "rebalance":
        if 40 <= score < 60:
            reasons.append(f"Score mediano: {score:.0f}/100 (grade {grade}) - zona de atenção")
        for flag in risk_flags:
            reasons.append(f"Flag: {flag.get('message', 'N/A')} ({flag.get('severity', 'medium')})")
        if score < avg_score - 10:
            reasons.append(f"Score {score - avg_score:.0f} pontos abaixo da média do portfólio ({avg_score:.0f})")
        if not reasons:
            reasons.append("Considerar redução de exposição ou substituição por projeto de maior qualidade")

    elif action == "hold":
        reasons.append(f"Score de qualidade sólido: {score:.0f}/100 (grade {grade})")
        if score >= 80:
            reasons.append("Projeto de alta qualidade - manter posição estratégica")
        if not risk_flags:
            reasons.append("Nenhuma flag de risco identificada")

    return reasons


def _generate_recommendations(positions: list, avg_score: float, type_dist: dict, country_dist: dict) -> list:
    """
    Gera recomendações de rebalanceamento do portfólio.
    DEDUPLICADO: recebe posições já agregadas por projeto.
    Cada recomendação inclui risk_flags e reasons detalhados.
    """
    recommendations = []
    priority = 1
    seen_project_ids = set()

    # Recomendação 1: Projetos com score muito baixo → VENDER
    for pos in sorted(positions, key=lambda x: x["score"]):
        if pos["score"] < 40 and pos["project_id"] not in seen_project_ids:
            seen_project_ids.add(pos["project_id"])
            risk_flags = _generate_risk_flag_summary(pos.get("risk_flags", []))
            reasons = _generate_reasons(pos, "sell", avg_score)
            recommendations.append({
                "project_id": pos["project_id"],
                "project_name": pos["project_name"],
                "project_type": pos.get("project_type", "N/A"),
                "country": pos.get("country", "N/A"),
                "registry": pos.get("registry", "N/A"),
                "current_grade": pos["grade"],
                "current_score": pos["score"],
                "total_quantity": pos.get("total_quantity", 0),
                "total_value": pos.get("total_value", 0),
                "action": "sell",
                "reason": f"Score de qualidade muito baixo ({pos['score']:.0f}/100). Risco elevado de desvalorização. Recomenda-se liquidar a posição.",
                "reasons": reasons,
                "risk_flags": risk_flags,
                "risk_level": "high",
                "priority": priority,
            })
            priority += 1

    # Recomendação 2: Projetos medianos → REBALANCEAR
    for pos in sorted(positions, key=lambda x: x["score"]):
        if 40 <= pos["score"] < 60 and pos["project_id"] not in seen_project_ids:
            seen_project_ids.add(pos["project_id"])
            risk_flags = _generate_risk_flag_summary(pos.get("risk_flags", []))
            reasons = _generate_reasons(pos, "rebalance", avg_score)
            recommendations.append({
                "project_id": pos["project_id"],
                "project_name": pos["project_name"],
                "project_type": pos.get("project_type", "N/A"),
                "country": pos.get("country", "N/A"),
                "registry": pos.get("registry", "N/A"),
                "current_grade": pos["grade"],
                "current_score": pos["score"],
                "total_quantity": pos.get("total_quantity", 0),
                "total_value": pos.get("total_value", 0),
                "action": "rebalance",
                "reason": f"Score de qualidade mediano ({pos['score']:.0f}/100). Considerar redução de exposição ou substituição por projetos de maior qualidade.",
                "reasons": reasons,
                "risk_flags": risk_flags,
                "risk_level": "medium",
                "priority": priority,
            })
            priority += 1

    # Recomendação 3: Concentração excessiva por tipo → REBALANCEAR
    total = sum(type_dist.values())
    if total > 0:
        for ptype, qty in sorted(type_dist.items(), key=lambda x: x[1], reverse=True):
            concentration = qty / total
            if concentration > 0.30:
                recommendations.append({
                    "project_id": None,
                    "project_name": f"Concentração: {ptype}",
                    "project_type": ptype,
                    "country": "N/A",
                    "registry": "N/A",
                    "current_grade": "N/A",
                    "current_score": 0,
                    "total_quantity": qty,
                    "total_value": 0,
                    "action": "rebalance",
                    "reason": f"Concentração de {concentration*100:.0f}% em {ptype}. Diversificar para reduzir risco setorial.",
                    "reasons": [
                        f"Concentração setorial de {concentration*100:.0f}% em {ptype}",
                        f"{qty:,} créditos concentrados em um único tipo de projeto",
                        "Recomenda-se diversificar para reduzir exposição a riscos regulatórios setoriais",
                    ],
                    "risk_flags": [{"type": "concentration_risk", "severity": "medium", "message": f"Concentração de {concentration*100:.0f}% em {ptype}"}],
                    "risk_level": "medium",
                    "priority": priority,
                })
                priority += 1

    # Recomendação 4: Concentração geográfica → REBALANCEAR
    if total > 0:
        for country, qty in sorted(country_dist.items(), key=lambda x: x[1], reverse=True):
            concentration = qty / total
            if concentration > 0.20:
                recommendations.append({
                    "project_id": None,
                    "project_name": f"Concentração: {country}",
                    "project_type": "N/A",
                    "country": country,
                    "registry": "N/A",
                    "current_grade": "N/A",
                    "current_score": 0,
                    "total_quantity": qty,
                    "total_value": 0,
                    "action": "rebalance",
                    "reason": f"Concentração geográfica de {concentration*100:.0f}% em {country}. Considerar diversificação regional.",
                    "reasons": [
                        f"Concentração geográfica de {concentration*100:.0f}% em {country}",
                        f"{qty:,} créditos concentrados em um único país",
                        "Risco regulatório e político concentrado - diversificar regionalmente",
                    ],
                    "risk_flags": [{"type": "geographic_concentration", "severity": "medium", "message": f"Concentração de {concentration*100:.0f}% em {country}"}],
                    "risk_level": "medium",
                    "priority": priority,
                })
                priority += 1

    # Recomendação 5: Projetos com bom score → MANTER
    for pos in sorted(positions, key=lambda x: x["score"], reverse=True):
        if pos["score"] >= 60 and pos["project_id"] not in seen_project_ids:
            seen_project_ids.add(pos["project_id"])
            risk_flags = _generate_risk_flag_summary(pos.get("risk_flags", []))
            reasons = _generate_reasons(pos, "hold", avg_score)
            recommendations.append({
                "project_id": pos["project_id"],
                "project_name": pos["project_name"],
                "project_type": pos.get("project_type", "N/A"),
                "country": pos.get("country", "N/A"),
                "registry": pos.get("registry", "N/A"),
                "current_grade": pos["grade"],
                "current_score": pos["score"],
                "total_quantity": pos.get("total_quantity", 0),
                "total_value": pos.get("total_value", 0),
                "action": "hold",
                "reason": f"Projeto com boa qualidade ({pos['score']:.0f}/100). Manter posição.",
                "reasons": reasons,
                "risk_flags": risk_flags,
                "risk_level": "low",
                "priority": priority,
            })
            priority += 1

    return recommendations


def group_recommendations_by_action(recommendations: list, page: int = 1, page_size: int = 20) -> dict:
    """
    Agrupa recomendações por ação para exibição em abas no frontend.
    Cada grupo inclui paginação server-side.
    """
    # Agrupar
    groups = {}
    for rec in recommendations:
        action = rec.get("action", "hold")
        if action not in groups:
            groups[action] = []
        groups[action].append(rec)

    # Ordenar cada grupo por prioridade
    for action in groups:
        groups[action].sort(key=lambda x: x.get("priority", 999))

    # Construir resposta com paginação por grupo
    result = {}
    for action, items in groups.items():
        total = len(items)
        total_pages = max(1, (total + page_size - 1) // page_size)
        offset = (page - 1) * page_size
        paginated = items[offset:offset + page_size]

        result[action] = {
            "items": paginated,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    return result


async def get_dashboard_metrics(db: AsyncSession, organization_id: int) -> dict:
    """Calcula métricas agregadas para o dashboard principal."""
    # Total de projetos
    proj_count = await db.execute(select(func.count(CarbonProject.id)))
    total_projects = proj_count.scalar() or 0

    # Total de créditos
    credit_count = await db.execute(select(func.sum(CarbonCredit.quantity)))
    total_credits = credit_count.scalar() or 0

    # Score médio
    avg_result = await db.execute(select(func.avg(ProjectRating.overall_score)))
    avg_score = avg_result.scalar() or 0

    # Distribuição de grades
    grade_result = await db.execute(
        select(ProjectRating.grade, func.count(ProjectRating.id))
        .group_by(ProjectRating.grade)
    )
    grade_distribution = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in grade_result.all()}

    # Alertas de fraude
    alert_count = await db.execute(select(func.count(FraudAlert.id)))
    total_alerts = alert_count.scalar() or 0

    severity_result = await db.execute(
        select(FraudAlert.severity, func.count(FraudAlert.id))
        .group_by(FraudAlert.severity)
    )
    alerts_by_severity = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in severity_result.all()}

    # Distribuição por tipo de projeto
    type_result = await db.execute(
        select(CarbonProject.project_type, func.count(CarbonProject.id))
        .group_by(CarbonProject.project_type)
    )
    type_distribution = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in type_result.all()}

    # Distribuição por país (top 10)
    country_result = await db.execute(
        select(CarbonProject.country, func.count(CarbonProject.id))
        .group_by(CarbonProject.country)
        .order_by(func.count(CarbonProject.id).desc())
        .limit(10)
    )
    country_distribution = {row[0]: row[1] for row in country_result.all()}

    # Valor total do portfólio
    portfolio_value = await db.execute(
        select(func.sum(PortfolioPosition.quantity * PortfolioPosition.acquisition_price_eur))
    )
    total_value = portfolio_value.scalar() or 0

    # Risk summary
    risk_result = await db.execute(
        select(
            func.sum(case((ProjectRating.overall_score < 40, 1), else_=0)),
            func.sum(case((ProjectRating.overall_score.between(40, 60), 1), else_=0)),
            func.sum(case((ProjectRating.overall_score > 60, 1), else_=0)),
        )
    )
    risk_row = risk_result.one()

    return {
        "total_projects": total_projects,
        "total_credits": total_credits,
        "avg_quality_score": round(float(avg_score), 2),
        "grade_distribution": grade_distribution,
        "risk_summary": {
            "high_risk": risk_row[0] or 0,
            "medium_risk": risk_row[1] or 0,
            "low_risk": risk_row[2] or 0,
        },
        "fraud_alerts_count": total_alerts,
        "fraud_alerts_by_severity": alerts_by_severity,
        "project_type_distribution": type_distribution,
        "country_distribution": country_distribution,
        "portfolio_value_eur": round(float(total_value), 2),
    }
