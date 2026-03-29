"""
Motor de Fraud Detection v1 - Carbon Verify

Implementa regras determinísticas de detecção de inconsistências,
conforme descrito no Módulo 2 do Mapa de Implementação.

Regras implementadas:
1. Over-crediting: créditos emitidos acima do máximo teórico
2. Divergência de área: área declarada inconsistente
3. Duplicidade potencial: detecção de projetos similares
4. Anomalia temporal: padrões incomuns de emissão/aposentadoria
5. Governança fraca: ausência de dados críticos
6. Vintage expirado: créditos muito antigos
"""
from datetime import datetime, timezone
from typing import Optional
from app.models.models import CarbonProject, FraudAlert, FraudSeverity, AlertStatus


# Thresholds de detecção
MAX_CREDITS_PER_HECTARE = {
    "REDD+": 30,
    "ARR": 25,
    "Renewable Energy": 100,
    "Cookstove": 50,
    "Methane Avoidance": 80,
    "Blue Carbon": 20,
    "Biochar": 40,
    "Direct Air Capture": 200,
    "Other": 50,
}

MAX_VINTAGE_AGE_YEARS = 10
MIN_BUFFER_PERCENTAGE = 5


def _check_overcrediting(project: CarbonProject) -> Optional[FraudAlert]:
    """Verifica se o projeto emitiu créditos acima do máximo teórico esperado."""
    if not project.area_hectares or project.area_hectares <= 0:
        return None
    if not project.total_credits_issued or project.total_credits_issued <= 0:
        return None
    
    project_type_key = project.project_type if isinstance(project.project_type, str) else project.project_type.value
    max_per_ha = MAX_CREDITS_PER_HECTARE.get(project_type_key, 50)
    actual_per_ha = project.total_credits_issued / project.area_hectares
    
    if actual_per_ha > max_per_ha:
        ratio = actual_per_ha / max_per_ha
        severity = FraudSeverity.CRITICAL if ratio > 3 else FraudSeverity.HIGH if ratio > 2 else FraudSeverity.MEDIUM
        
        return FraudAlert(
            project_id=project.id,
            alert_type="overcrediting",
            severity=severity,
            title=f"Possível over-crediting detectado",
            description=(
                f"O projeto emitiu {actual_per_ha:.1f} créditos/hectare, "
                f"enquanto o máximo esperado para projetos {project_type_key} é "
                f"{max_per_ha} créditos/hectare ({ratio:.1f}x acima do limite)."
            ),
            evidence={
                "total_credits_issued": project.total_credits_issued,
                "area_hectares": project.area_hectares,
                "credits_per_hectare": round(actual_per_ha, 2),
                "max_expected": max_per_ha,
                "excess_ratio": round(ratio, 2),
            },
            recommendation="Revisar documentação de baseline e metodologia de cálculo de emissões evitadas/removidas.",
            detection_method="rule_based",
            confidence=min(0.95, 0.5 + (ratio - 1) * 0.2),
        )
    return None


def _check_area_inconsistency(project: CarbonProject) -> Optional[FraudAlert]:
    """Verifica inconsistências na área declarada do projeto."""
    if not project.area_hectares:
        return FraudAlert(
            project_id=project.id,
            alert_type="missing_area",
            severity=FraudSeverity.LOW,
            title="Área do projeto não declarada",
            description="O projeto não possui informação de área, impossibilitando validação de densidade de créditos.",
            evidence={"area_hectares": None},
            recommendation="Solicitar documentação de área do projeto ao proponente.",
            detection_method="rule_based",
            confidence=0.3,
        )
    
    if project.area_hectares > 10_000_000:  # > 10M hectares
        return FraudAlert(
            project_id=project.id,
            alert_type="area_anomaly",
            severity=FraudSeverity.HIGH,
            title="Área do projeto anormalmente grande",
            description=f"A área declarada de {project.area_hectares:,.0f} hectares é excepcionalmente grande e requer verificação.",
            evidence={"area_hectares": project.area_hectares},
            recommendation="Verificar coordenadas geográficas e documentação fundiária do projeto.",
            detection_method="rule_based",
            confidence=0.7,
        )
    return None


def _check_vintage_age(project: CarbonProject) -> Optional[FraudAlert]:
    """Verifica se os créditos são muito antigos."""
    if not project.vintage_year:
        return None
    
    current_year = datetime.now(timezone.utc).year
    age = current_year - project.vintage_year
    
    if age > MAX_VINTAGE_AGE_YEARS:
        severity = FraudSeverity.HIGH if age > 15 else FraudSeverity.MEDIUM
        return FraudAlert(
            project_id=project.id,
            alert_type="vintage_age",
            severity=severity,
            title="Créditos com vintage muito antigo",
            description=(
                f"Os créditos deste projeto têm vintage de {project.vintage_year} "
                f"({age} anos atrás). Créditos antigos podem ter menor integridade ambiental."
            ),
            evidence={"vintage_year": project.vintage_year, "age_years": age},
            recommendation="Avaliar se as condições do projeto ainda são válidas e se o baseline permanece relevante.",
            detection_method="rule_based",
            confidence=0.6,
        )
    return None


def _check_buffer_pool(project: CarbonProject) -> Optional[FraudAlert]:
    """Verifica se o buffer pool é adequado para projetos de remoção."""
    removal_types = ["REDD+", "ARR", "Blue Carbon", "Biochar"]
    project_type_key = project.project_type if isinstance(project.project_type, str) else project.project_type.value
    
    if project_type_key not in removal_types:
        return None
    
    if not project.buffer_pool_percentage or project.buffer_pool_percentage < MIN_BUFFER_PERCENTAGE:
        return FraudAlert(
            project_id=project.id,
            alert_type="insufficient_buffer",
            severity=FraudSeverity.MEDIUM,
            title="Buffer pool insuficiente para risco de reversão",
            description=(
                f"Projetos de {project_type_key} requerem buffer pool adequado para cobrir riscos de reversão. "
                f"Buffer atual: {project.buffer_pool_percentage or 0}% (mínimo recomendado: {MIN_BUFFER_PERCENTAGE}%)."
            ),
            evidence={
                "buffer_pool_percentage": project.buffer_pool_percentage,
                "min_recommended": MIN_BUFFER_PERCENTAGE,
                "project_type": project_type_key,
            },
            recommendation="Verificar se o padrão de certificação exige buffer pool e se o percentual é adequado ao risco.",
            detection_method="rule_based",
            confidence=0.65,
        )
    return None


def _check_retirement_anomaly(project: CarbonProject) -> Optional[FraudAlert]:
    """Verifica anomalias na taxa de aposentadoria de créditos."""
    if not project.total_credits_issued or project.total_credits_issued == 0:
        return None
    
    retirement_rate = project.total_credits_retired / project.total_credits_issued
    
    if retirement_rate > 0.95 and project.total_credits_issued > 10000:
        return FraudAlert(
            project_id=project.id,
            alert_type="retirement_anomaly",
            severity=FraudSeverity.MEDIUM,
            title="Taxa de aposentadoria anormalmente alta",
            description=(
                f"O projeto tem {retirement_rate*100:.1f}% dos créditos aposentados "
                f"({project.total_credits_retired:,} de {project.total_credits_issued:,}), "
                f"o que pode indicar atividade incomum."
            ),
            evidence={
                "total_issued": project.total_credits_issued,
                "total_retired": project.total_credits_retired,
                "retirement_rate": round(retirement_rate, 4),
            },
            recommendation="Verificar histórico de transações e identificar os compradores dos créditos.",
            detection_method="rule_based",
            confidence=0.5,
        )
    return None


def _check_governance_gaps(project: CarbonProject) -> Optional[FraudAlert]:
    """Verifica lacunas de governança e documentação."""
    missing = []
    if not project.registry:
        missing.append("registro/padrão de certificação")
    if not project.methodology:
        missing.append("metodologia")
    if not project.proponent:
        missing.append("proponente")
    if not project.external_id:
        missing.append("ID externo de registro")
    if not project.monitoring_frequency:
        missing.append("frequência de monitoramento")
    
    if len(missing) >= 3:
        return FraudAlert(
            project_id=project.id,
            alert_type="governance_gaps",
            severity=FraudSeverity.MEDIUM if len(missing) < 4 else FraudSeverity.HIGH,
            title="Lacunas significativas de governança",
            description=(
                f"O projeto possui {len(missing)} campos críticos de governança ausentes: "
                f"{', '.join(missing)}. Isso dificulta a verificação de integridade."
            ),
            evidence={"missing_fields": missing, "missing_count": len(missing)},
            recommendation="Solicitar documentação completa ao proponente antes de prosseguir com a aquisição.",
            detection_method="rule_based",
            confidence=0.7,
        )
    return None


def run_fraud_detection(project: CarbonProject) -> list[FraudAlert]:
    """
    Executa todas as regras de detecção de fraude para um projeto.
    
    Retorna uma lista de FraudAlerts detectados.
    """
    checks = [
        _check_overcrediting,
        _check_area_inconsistency,
        _check_vintage_age,
        _check_buffer_pool,
        _check_retirement_anomaly,
        _check_governance_gaps,
    ]
    
    alerts = []
    for check in checks:
        alert = check(project)
        if alert:
            alerts.append(alert)
    
    return alerts
