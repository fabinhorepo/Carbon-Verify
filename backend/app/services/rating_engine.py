"""
Motor de Rating de Qualidade v1 - Carbon Verify

Implementa um scorecard baseado em regras com 7 dimensões de avaliação,
conforme descrito no Módulo 1 do Mapa de Implementação.

Dimensões:
1. Integridade do Baseline
2. Adicionalidade
3. Permanência
4. Leakage (Vazamento)
5. MRV (Measurement, Reporting, Verification)
6. Co-benefícios
7. Governança

Cada dimensão produz um sub-score de 0-100.
O score final é a média ponderada dos sub-scores.
O grade AAA-D é derivado do score final.

Distribuição esperada com o seed data:
  - 60% projetos bons (score > 60, grades A-AA)
  - 30% projetos medianos (score 40-60, grades BB-BBB)
  - 10% projetos ruins (score < 40, grades D-B)
"""
from typing import Optional
from app.models.models import CarbonProject, ProjectRating, RatingGrade


# Pesos das dimensões no score final
DIMENSION_WEIGHTS = {
    "additionality": 0.20,
    "permanence": 0.18,
    "baseline_integrity": 0.15,
    "leakage": 0.12,
    "mrv": 0.15,
    "co_benefits": 0.10,
    "governance": 0.10,
}

# Fronteiras de decisão para grades
GRADE_BOUNDARIES = [
    (90, RatingGrade.AAA),
    (80, RatingGrade.AA),
    (70, RatingGrade.A),
    (60, RatingGrade.BBB),
    (50, RatingGrade.BB),
    (40, RatingGrade.B),
    (30, RatingGrade.CCC),
    (20, RatingGrade.CC),
    (10, RatingGrade.C),
    (0, RatingGrade.D),
]

# Scores base por tipo de projeto (heurísticas de mercado)
# Estes são os scores BASE antes de bônus/penalidades por documentação
PROJECT_TYPE_BASE_SCORES = {
    "REDD+": {"additionality": 35, "permanence": 30, "leakage": 30, "mrv": 35, "co_benefits": 45, "governance": 30, "baseline_integrity": 35},
    "ARR": {"additionality": 40, "permanence": 35, "leakage": 35, "mrv": 40, "co_benefits": 50, "governance": 35, "baseline_integrity": 40},
    "Renewable Energy": {"additionality": 30, "permanence": 50, "leakage": 50, "mrv": 45, "co_benefits": 25, "governance": 40, "baseline_integrity": 40},
    "Cookstove": {"additionality": 35, "permanence": 40, "leakage": 45, "mrv": 30, "co_benefits": 50, "governance": 30, "baseline_integrity": 35},
    "Methane Avoidance": {"additionality": 45, "permanence": 50, "leakage": 55, "mrv": 40, "co_benefits": 30, "governance": 35, "baseline_integrity": 45},
    "Blue Carbon": {"additionality": 40, "permanence": 30, "leakage": 30, "mrv": 30, "co_benefits": 55, "governance": 30, "baseline_integrity": 35},
    "Biochar": {"additionality": 50, "permanence": 55, "leakage": 60, "mrv": 40, "co_benefits": 30, "governance": 35, "baseline_integrity": 45},
    "Direct Air Capture": {"additionality": 60, "permanence": 65, "leakage": 65, "mrv": 50, "co_benefits": 20, "governance": 40, "baseline_integrity": 55},
    "Other": {"additionality": 25, "permanence": 25, "leakage": 25, "mrv": 25, "co_benefits": 25, "governance": 25, "baseline_integrity": 25},
}

# Modificadores por registro
REGISTRY_MODIFIERS = {
    "Verra": 5,
    "Gold Standard": 8,
    "ACR": 4,
    "CAR": 4,
    "Plan Vivo": 6,
}


def _score_additionality(project: CarbonProject, base: float) -> float:
    """Avalia adicionalidade financeira e regulatória."""
    score = base
    if project.additionality_justification:
        text_len = len(project.additionality_justification)
        if text_len > 300:
            score += 30
        elif text_len > 100:
            score += 20
        elif text_len > 30:
            score += 10
    else:
        score -= 15  # Penalidade por falta de justificativa
    if project.methodology:
        score += 10
    else:
        score -= 10
    return min(100, max(0, score))


def _score_permanence(project: CarbonProject, base: float) -> float:
    """Avalia risco de reversão e permanência."""
    score = base
    if project.buffer_pool_percentage:
        if project.buffer_pool_percentage >= 20:
            score += 25
        elif project.buffer_pool_percentage >= 15:
            score += 20
        elif project.buffer_pool_percentage >= 10:
            score += 15
        elif project.buffer_pool_percentage >= 5:
            score += 8
        else:
            score -= 5  # Buffer insuficiente
    else:
        # Projetos de remoção sem buffer = penalidade
        ptype = project.project_type if isinstance(project.project_type, str) else project.project_type.value
        if ptype in ("REDD+", "ARR", "Blue Carbon"):
            score -= 10
    if project.end_date and project.start_date:
        duration_years = (project.end_date - project.start_date).days / 365
        if duration_years >= 30:
            score += 15
        elif duration_years >= 20:
            score += 10
        elif duration_years >= 10:
            score += 5
        else:
            score -= 5  # Projeto muito curto
    return min(100, max(0, score))


def _score_leakage(project: CarbonProject, base: float) -> float:
    """Avalia risco de vazamento de emissões."""
    score = base
    if project.area_hectares:
        if project.area_hectares > 100000:
            score -= 5
        elif project.area_hectares < 1000:
            score += 5
    if project.baseline_scenario:
        text_len = len(project.baseline_scenario)
        if text_len > 200:
            score += 15
        elif text_len > 50:
            score += 8
    else:
        score -= 10
    if project.methodology:
        score += 5
    return min(100, max(0, score))


def _score_mrv(project: CarbonProject, base: float) -> float:
    """Avalia qualidade de Medição, Reporte e Verificação."""
    score = base
    if project.monitoring_frequency:
        freq = project.monitoring_frequency.lower()
        if "quarterly" in freq or "trimestral" in freq:
            score += 30
        elif "biannual" in freq or "semestral" in freq:
            score += 25
        elif "annual" in freq or "anual" in freq:
            score += 15
    else:
        score -= 15  # Sem monitoramento
    if project.methodology:
        score += 10
    else:
        score -= 10
    return min(100, max(0, score))


def _score_co_benefits(project: CarbonProject, base: float) -> float:
    """Avalia co-benefícios sociais e ambientais."""
    score = base
    developing_regions = [
        "Brazil", "India", "Indonesia", "Kenya", "Colombia", "Peru",
        "Congo", "Ethiopia", "Vietnam", "Cambodia", "Uganda", "Rwanda",
        "Ghana", "Malawi", "Tanzania", "Mozambique", "Bangladesh", "Nepal",
        "Honduras", "Nicaragua", "Senegal", "Mali", "Burkina Faso",
        "Madagascar", "Myanmar", "Philippines", "Guatemala", "Mexico",
        "Zambia",
    ]
    if project.country in developing_regions:
        score += 10
    if project.description and len(project.description) > 200:
        score += 10
    elif project.description and len(project.description) > 50:
        score += 5
    else:
        score -= 5
    return min(100, max(0, score))


def _score_governance(project: CarbonProject, base: float) -> float:
    """Avalia governança do projeto."""
    score = base
    if project.proponent:
        score += 10
    else:
        score -= 15  # Sem proponente identificado
    registry_mod = REGISTRY_MODIFIERS.get(project.registry, 0)
    score += registry_mod
    if project.external_id:
        score += 5
    if project.methodology:
        score += 5
    else:
        score -= 10
    return min(100, max(0, score))


def _score_baseline_integrity(project: CarbonProject, base: float) -> float:
    """Avalia integridade do cenário de baseline."""
    score = base
    if project.baseline_scenario:
        text_len = len(project.baseline_scenario)
        if text_len > 300:
            score += 25
        elif text_len > 100:
            score += 15
        elif text_len > 30:
            score += 8
    else:
        score -= 15  # Sem baseline
    if project.total_credits_issued > 0 and project.area_hectares:
        credits_per_ha = project.total_credits_issued / project.area_hectares
        if credits_per_ha > 50:
            score -= 15  # Muito agressivo
        elif credits_per_ha > 30:
            score -= 5
        elif credits_per_ha < 5:
            score += 5  # Conservador
    if project.methodology:
        score += 5
    return min(100, max(0, score))


def _get_grade(score: float) -> RatingGrade:
    """Converte score numérico em grade AAA-D."""
    for threshold, grade in GRADE_BOUNDARIES:
        if score >= threshold:
            return grade
    return RatingGrade.D


def _generate_explanation(project: CarbonProject, sub_scores: dict, grade: RatingGrade) -> str:
    """Gera explicação textual do rating."""
    strengths = []
    weaknesses = []

    for dim, score in sub_scores.items():
        label = dim.replace("_", " ").title()
        if score >= 75:
            strengths.append(f"{label} ({score:.0f}/100)")
        elif score < 50:
            weaknesses.append(f"{label} ({score:.0f}/100)")

    explanation = f"O projeto '{project.name}' recebeu rating {grade.value} "
    explanation += f"com base na análise de 7 dimensões de qualidade. "

    if strengths:
        explanation += f"Pontos fortes: {', '.join(strengths)}. "
    if weaknesses:
        explanation += f"Áreas de atenção: {', '.join(weaknesses)}. "

    explanation += f"Tipo de projeto: {project.project_type}. "
    if project.registry:
        explanation += f"Registro: {project.registry}. "

    return explanation


def _generate_risk_flags(project: CarbonProject, sub_scores: dict) -> list:
    """Gera flags de risco baseados nos sub-scores."""
    flags = []

    if sub_scores["permanence"] < 40:
        flags.append({"type": "permanence_risk", "severity": "high", "message": "Alto risco de reversão identificado"})

    if sub_scores["leakage"] < 40:
        flags.append({"type": "leakage_risk", "severity": "high", "message": "Risco significativo de vazamento de emissões"})

    if sub_scores["additionality"] < 40:
        flags.append({"type": "additionality_concern", "severity": "high", "message": "Adicionalidade questionável"})

    if sub_scores["mrv"] < 50:
        flags.append({"type": "mrv_weakness", "severity": "medium", "message": "Sistema MRV pode ser insuficiente"})

    if sub_scores["governance"] < 40:
        flags.append({"type": "governance_concern", "severity": "medium", "message": "Governança do projeto precisa de atenção"})

    if project.total_credits_issued > 0 and project.area_hectares:
        ratio = project.total_credits_issued / max(project.area_hectares, 1)
        if ratio > 50:
            flags.append({"type": "overcrediting_risk", "severity": "high", "message": f"Taxa de créditos/hectare ({ratio:.1f}) acima do esperado"})

    if not project.registry:
        flags.append({"type": "no_registry", "severity": "medium", "message": "Projeto sem registro em padrão reconhecido"})

    return flags


def calculate_rating(project: CarbonProject) -> ProjectRating:
    """
    Calcula o rating completo de um projeto de carbono.

    Retorna um objeto ProjectRating com score final, grade,
    sub-scores, explicação e flags de risco.
    """
    project_type_key = project.project_type if isinstance(project.project_type, str) else project.project_type.value
    base_scores = PROJECT_TYPE_BASE_SCORES.get(project_type_key, PROJECT_TYPE_BASE_SCORES["Other"])

    sub_scores = {
        "additionality": _score_additionality(project, base_scores["additionality"]),
        "permanence": _score_permanence(project, base_scores["permanence"]),
        "leakage": _score_leakage(project, base_scores["leakage"]),
        "mrv": _score_mrv(project, base_scores["mrv"]),
        "co_benefits": _score_co_benefits(project, base_scores["co_benefits"]),
        "governance": _score_governance(project, base_scores["governance"]),
        "baseline_integrity": _score_baseline_integrity(project, base_scores["baseline_integrity"]),
    }

    overall_score = sum(
        sub_scores[dim] * weight
        for dim, weight in DIMENSION_WEIGHTS.items()
    )

    grade = _get_grade(overall_score)

    data_fields = [
        project.methodology, project.registry, project.baseline_scenario,
        project.additionality_justification, project.monitoring_frequency,
        project.buffer_pool_percentage, project.area_hectares, project.proponent,
        project.external_id, project.description,
    ]
    filled = sum(1 for f in data_fields if f)
    confidence = filled / len(data_fields)

    explanation = _generate_explanation(project, sub_scores, grade)
    risk_flags = _generate_risk_flags(project, sub_scores)

    return ProjectRating(
        project_id=project.id,
        overall_score=round(overall_score, 2),
        grade=grade,
        additionality_score=round(sub_scores["additionality"], 2),
        permanence_score=round(sub_scores["permanence"], 2),
        leakage_score=round(sub_scores["leakage"], 2),
        mrv_score=round(sub_scores["mrv"], 2),
        co_benefits_score=round(sub_scores["co_benefits"], 2),
        governance_score=round(sub_scores["governance"], 2),
        baseline_integrity_score=round(sub_scores["baseline_integrity"], 2),
        confidence_level=round(confidence, 2),
        explanation=explanation,
        risk_flags=risk_flags,
    )
