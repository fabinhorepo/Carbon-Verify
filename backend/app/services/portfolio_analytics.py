"""
Serviço de Analytics de Portfólio - Carbon Verify

Implementa cálculos de métricas de risco, qualidade e
recomendações de rebalanceamento conforme Módulo 3.
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
    # Buscar posições com créditos e projetos
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
            "total_value_usd": 0,
            "avg_quality_score": 0,
            "grade_distribution": {},
            "risk_exposure": {},
            "project_type_distribution": {},
            "country_distribution": {},
            "recommendations": [],
        }
    
    total_credits = 0
    total_value = 0
    weighted_score_sum = 0
    grade_dist = {}
    type_dist = {}
    country_dist = {}
    risk_exposure = {"high": 0, "medium": 0, "low": 0}
    project_details = []
    
    for position, credit, project, rating in rows:
        qty = position.quantity
        total_credits += qty
        
        price = position.acquisition_price_usd or credit.price_usd or 0
        total_value += qty * price
        
        score = rating.overall_score if rating else 50
        grade = rating.grade.value if rating else "N/A"
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
        
        project_details.append({
            "position_id": position.id,
            "project_id": project.id,
            "project_name": project.name,
            "project_type": ptype,
            "country": project.country,
            "quantity": qty,
            "score": score,
            "grade": grade,
            "price_usd": price,
        })
    
    avg_score = weighted_score_sum / total_credits if total_credits > 0 else 0
    
    # Gerar recomendações
    recommendations = _generate_recommendations(project_details, avg_score, type_dist, country_dist)
    
    return {
        "total_credits": total_credits,
        "total_value_usd": round(total_value, 2),
        "avg_quality_score": round(avg_score, 2),
        "grade_distribution": grade_dist,
        "risk_exposure": risk_exposure,
        "project_type_distribution": type_dist,
        "country_distribution": country_dist,
        "recommendations": recommendations,
        "positions": project_details,
    }


def _generate_recommendations(positions: list, avg_score: float, type_dist: dict, country_dist: dict) -> list:
    """Gera recomendações de rebalanceamento do portfólio."""
    recommendations = []
    priority = 1
    
    # Recomendação 1: Projetos com score muito baixo → VENDER
    for pos in sorted(positions, key=lambda x: x["score"]):
        if pos["score"] < 40:
            recommendations.append({
                "project_id": pos["project_id"],
                "project_name": pos["project_name"],
                "current_grade": pos["grade"],
                "current_score": pos["score"],
                "action": "sell",
                "reason": f"Score de qualidade muito baixo ({pos['score']:.0f}/100). Risco elevado de desvalorização. Recomenda-se liquidar a posição.",
                "risk_level": "high",
                "priority": priority,
            })
            priority += 1

    # Recomendação 2: Projetos medianos → REBALANCEAR
    for pos in sorted(positions, key=lambda x: x["score"]):
        if 40 <= pos["score"] < 60:
            recommendations.append({
                "project_id": pos["project_id"],
                "project_name": pos["project_name"],
                "current_grade": pos["grade"],
                "current_score": pos["score"],
                "action": "rebalance",
                "reason": f"Score de qualidade mediano ({pos['score']:.0f}/100). Considerar redução de exposição ou substituição por projetos de maior qualidade.",
                "risk_level": "medium",
                "priority": priority,
            })
            priority += 1

    # Recomendação 3: Concentração excessiva por tipo → REBALANCEAR
    total = sum(type_dist.values())
    if total > 0:
        for ptype, qty in type_dist.items():
            concentration = qty / total
            if concentration > 0.30:
                recommendations.append({
                    "project_id": None,
                    "project_name": f"Tipo: {ptype}",
                    "current_grade": "N/A",
                    "current_score": 0,
                    "action": "rebalance",
                    "reason": f"Concentração de {concentration*100:.0f}% em {ptype}. Diversificar para reduzir risco setorial.",
                    "risk_level": "medium",
                    "priority": priority,
                })
                priority += 1

    # Recomendação 4: Concentração geográfica → REBALANCEAR
    if total > 0:
        for country, qty in country_dist.items():
            concentration = qty / total
            if concentration > 0.20:
                recommendations.append({
                    "project_id": None,
                    "project_name": f"País: {country}",
                    "current_grade": "N/A",
                    "current_score": 0,
                    "action": "rebalance",
                    "reason": f"Concentração geográfica de {concentration*100:.0f}% em {country}. Considerar diversificação regional.",
                    "risk_level": "medium",
                    "priority": priority,
                })
                priority += 1

    # Recomendação 5: Projetos com bom score → MANTER
    for pos in sorted(positions, key=lambda x: x["score"], reverse=True):
        if pos["score"] >= 60:
            recommendations.append({
                "project_id": pos["project_id"],
                "project_name": pos["project_name"],
                "current_grade": pos["grade"],
                "current_score": pos["score"],
                "action": "hold",
                "reason": f"Projeto com boa qualidade ({pos['score']:.0f}/100). Manter posição.",
                "risk_level": "low",
                "priority": priority,
            })
            priority += 1
    
    return recommendations


def group_recommendations_by_action(recommendations: list) -> dict:
    """Agrupa recomendações por ação para exibição em abas no frontend."""
    grouped = {}
    for rec in recommendations:
        action = rec.get("action", "hold")
        if action not in grouped:
            grouped[action] = []
        grouped[action].append(rec)
    # Ordenar cada grupo por prioridade
    for action in grouped:
        grouped[action].sort(key=lambda x: x.get("priority", 999))
    return grouped


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
    
    # Distribuição por país
    country_result = await db.execute(
        select(CarbonProject.country, func.count(CarbonProject.id))
        .group_by(CarbonProject.country)
        .order_by(func.count(CarbonProject.id).desc())
        .limit(10)
    )
    country_distribution = {row[0]: row[1] for row in country_result.all()}
    
    # Valor total do portfólio
    portfolio_value = await db.execute(
        select(func.sum(PortfolioPosition.quantity * PortfolioPosition.acquisition_price_usd))
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
        "portfolio_value_usd": round(float(total_value), 2),
    }
