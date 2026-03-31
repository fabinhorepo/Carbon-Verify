"""
Testes unitários para o Fraud Detection Engine v1.
Verifica detecção de alertas por tipo e severidade.
"""
import pytest
from datetime import date
from unittest.mock import MagicMock
from app.services.fraud_detection import run_fraud_detection


def _make_project(**kwargs):
    """Cria um mock de CarbonProject."""
    defaults = {
        "id": 1,
        "name": "Test Project",
        "project_type": "REDD+",
        "registry": "Verra",
        "country": "Brazil",
        "total_credits_issued": 100000,
        "total_credits_retired": 50000,
        "area_hectares": 50000.0,
        "buffer_pool_percentage": 15.0,
        "proponent": "Test Corp",
        "methodology": "VM0015",
        "monitoring_frequency": "Annual",
        "external_id": "VCS-001",
        "vintage_year": 2023,
        "start_date": date(2015, 1, 1),
        "end_date": date(2050, 12, 31),
    }
    defaults.update(kwargs)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def _make_credit(**kwargs):
    """Cria um mock de CarbonCredit."""
    defaults = {
        "id": 1,
        "project_id": 1,
        "vintage_year": 2023,
        "quantity": 50000,
        "serial_number": "VCS-001-2023",
        "status": "active",
        "retirement_date": None,
        "issuance_date": date(2023, 6, 1),
    }
    defaults.update(kwargs)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


class TestOvercrediting:
    """Testa detecção de overcrediting."""

    def test_overcrediting_detected(self):
        """Projeto com muitos créditos por hectare deve gerar alerta."""
        project = _make_project(total_credits_issued=1000000, area_hectares=5000)
        credits = [_make_credit()]
        alerts = run_fraud_detection(project)
        overcrediting = [a for a in alerts if a.alert_type == "overcrediting"]
        assert len(overcrediting) > 0, "Deveria detectar overcrediting"
        assert overcrediting[0].severity in ("high", "critical")

    def test_no_overcrediting_normal_ratio(self):
        """Projeto com ratio normal não deve gerar alerta de overcrediting."""
        project = _make_project(total_credits_issued=100000, area_hectares=50000)
        credits = [_make_credit()]
        alerts = run_fraud_detection(project)
        overcrediting = [a for a in alerts if a.alert_type == "overcrediting"]
        assert len(overcrediting) == 0, "Não deveria detectar overcrediting"


class TestVintageAge:
    """Testa detecção de créditos com vintage antigo."""

    def test_old_vintage_detected(self):
        """Projeto com vintage muito antigo deve gerar alerta."""
        project = _make_project(vintage_year=2010)
        alerts = run_fraud_detection(project)
        vintage = [a for a in alerts if a.alert_type == "vintage_age"]
        assert len(vintage) > 0, "Deveria detectar vintage antigo"

    def test_recent_vintage_ok(self):
        """Projeto com vintage recente não deve gerar alerta."""
        project = _make_project(vintage_year=2024)
        alerts = run_fraud_detection(project)
        vintage = [a for a in alerts if a.alert_type == "vintage_age"]
        assert len(vintage) == 0, "Não deveria detectar vintage antigo"


class TestMissingArea:
    """Testa detecção de projetos sem área definida."""

    def test_missing_area_detected(self):
        """Projeto de remoção sem área deve gerar alerta."""
        project = _make_project(area_hectares=None, project_type="REDD+")
        credits = [_make_credit()]
        alerts = run_fraud_detection(project)
        missing = [a for a in alerts if a.alert_type == "missing_area"]
        assert len(missing) > 0, "Deveria detectar área faltante"

    def test_area_present_ok(self):
        """Projeto com área não deve gerar alerta de missing_area."""
        project = _make_project(area_hectares=50000)
        credits = [_make_credit()]
        alerts = run_fraud_detection(project)
        missing = [a for a in alerts if a.alert_type == "missing_area"]
        assert len(missing) == 0, "Não deveria detectar área faltante"


class TestGovernanceGaps:
    """Testa detecção de lacunas de governança."""

    def test_governance_gaps_multiple_missing(self):
        """Projeto com >= 3 campos de governança faltantes deve gerar alerta."""
        project = _make_project(
            proponent=None, methodology=None, registry=None,
            external_id=None, monitoring_frequency=None,
        )
        alerts = run_fraud_detection(project)
        governance = [a for a in alerts if a.alert_type == "governance_gaps"]
        assert len(governance) > 0, "Deveria detectar lacuna de governança"

    def test_governance_ok_with_enough_fields(self):
        """Projeto com campos de governança preenchidos não deve gerar alerta."""
        project = _make_project()  # Tem todos os campos preenchidos
        alerts = run_fraud_detection(project)
        governance = [a for a in alerts if a.alert_type == "governance_gaps"]
        assert len(governance) == 0, "Não deveria detectar lacuna de governança"


class TestBufferPool:
    """Testa detecção de buffer insuficiente."""

    def test_insufficient_buffer(self):
        """Projeto de remoção com buffer baixo deve gerar alerta."""
        project = _make_project(buffer_pool_percentage=2.0, project_type="REDD+")
        credits = [_make_credit()]
        alerts = run_fraud_detection(project)
        buffer = [a for a in alerts if a.alert_type == "insufficient_buffer"]
        assert len(buffer) > 0, "Deveria detectar buffer insuficiente"

    def test_adequate_buffer_ok(self):
        """Projeto com buffer adequado não deve gerar alerta."""
        project = _make_project(buffer_pool_percentage=20.0)
        credits = [_make_credit()]
        alerts = run_fraud_detection(project)
        buffer = [a for a in alerts if a.alert_type == "insufficient_buffer"]
        assert len(buffer) == 0, "Não deveria detectar buffer insuficiente"


class TestAlertStructure:
    """Testa estrutura dos alertas gerados."""

    def test_alert_has_required_fields(self):
        """Cada alerta deve ter os campos obrigatórios."""
        project = _make_project(total_credits_issued=1000000, area_hectares=1000, vintage_year=2010)
        alerts = run_fraud_detection(project)
        assert len(alerts) > 0
        for alert in alerts:
            assert hasattr(alert, 'alert_type')
            assert hasattr(alert, 'severity')
            assert hasattr(alert, 'title')
            assert hasattr(alert, 'description')
            assert alert.severity in ("low", "medium", "high", "critical")

    def test_multiple_alerts_for_bad_project(self):
        """Projeto problemático deve gerar múltiplos alertas."""
        project = _make_project(
            total_credits_issued=5000000,
            area_hectares=None,
            buffer_pool_percentage=1.0,
            proponent=None,
            methodology=None,
            registry=None,
            external_id=None,
            monitoring_frequency=None,
            vintage_year=2008,
            project_type="REDD+",
        )
        alerts = run_fraud_detection(project)
        alert_types = {a.alert_type for a in alerts}
        assert len(alert_types) >= 3, f"Deveria gerar >= 3 tipos de alerta, gerou {len(alert_types)}: {alert_types}"
