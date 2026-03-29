"""
Testes unitários para o Rating Engine v1.
Verifica cálculo de scores, grades e distribuição de qualidade.
"""
import pytest
from datetime import date
from unittest.mock import MagicMock
from app.services.rating_engine import (
    calculate_rating, _get_grade, _score_additionality,
    _score_permanence, _score_leakage, _score_mrv,
    _score_co_benefits, _score_governance, _score_baseline_integrity,
    DIMENSION_WEIGHTS, GRADE_BOUNDARIES,
)
from app.models.models import RatingGrade


def _make_project(**kwargs):
    """Cria um mock de CarbonProject para testes."""
    defaults = {
        "id": 1,
        "name": "Test Project",
        "project_type": "REDD+",
        "registry": "Verra",
        "country": "Brazil",
        "methodology": "VM0015",
        "baseline_scenario": "Deforestation baseline scenario with detailed analysis " * 10,
        "additionality_justification": "Financial additionality demonstrated through IRR analysis " * 10,
        "monitoring_frequency": "Annual",
        "buffer_pool_percentage": 15.0,
        "area_hectares": 50000.0,
        "total_credits_issued": 500000,
        "proponent": "Test Corp",
        "external_id": "VCS-001",
        "description": "A comprehensive REDD+ project " * 20,
        "start_date": date(2015, 1, 1),
        "end_date": date(2050, 12, 31),
    }
    defaults.update(kwargs)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


class TestGradeBoundaries:
    """Testa conversão de score para grade."""

    def test_aaa_grade(self):
        assert _get_grade(95) == RatingGrade.AAA

    def test_aa_grade(self):
        assert _get_grade(85) == RatingGrade.AA

    def test_a_grade(self):
        assert _get_grade(75) == RatingGrade.A

    def test_bbb_grade(self):
        assert _get_grade(65) == RatingGrade.BBB

    def test_bb_grade(self):
        assert _get_grade(55) == RatingGrade.BB

    def test_b_grade(self):
        assert _get_grade(45) == RatingGrade.B

    def test_ccc_grade(self):
        assert _get_grade(35) == RatingGrade.CCC

    def test_cc_grade(self):
        assert _get_grade(25) == RatingGrade.CC

    def test_c_grade(self):
        assert _get_grade(15) == RatingGrade.C

    def test_d_grade(self):
        assert _get_grade(5) == RatingGrade.D

    def test_boundary_exact(self):
        assert _get_grade(90) == RatingGrade.AAA
        assert _get_grade(80) == RatingGrade.AA
        assert _get_grade(70) == RatingGrade.A
        assert _get_grade(60) == RatingGrade.BBB
        assert _get_grade(50) == RatingGrade.BB
        assert _get_grade(40) == RatingGrade.B
        assert _get_grade(30) == RatingGrade.CCC
        assert _get_grade(20) == RatingGrade.CC
        assert _get_grade(10) == RatingGrade.C
        assert _get_grade(0) == RatingGrade.D


class TestDimensionWeights:
    """Testa que os pesos das dimensões somam 1.0."""

    def test_weights_sum_to_one(self):
        total = sum(DIMENSION_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001, f"Pesos somam {total}, esperado 1.0"

    def test_all_dimensions_present(self):
        expected = {"additionality", "permanence", "baseline_integrity", "leakage", "mrv", "co_benefits", "governance"}
        assert set(DIMENSION_WEIGHTS.keys()) == expected


class TestSubScores:
    """Testa cálculo individual de cada sub-score."""

    def test_additionality_with_full_docs(self):
        project = _make_project(additionality_justification="x" * 500, methodology="VM0015")
        score = _score_additionality(project, 35)
        assert score >= 65, f"Score {score} deveria ser >= 65 com docs completos"

    def test_additionality_without_docs(self):
        project = _make_project(additionality_justification=None, methodology=None)
        score = _score_additionality(project, 35)
        assert score <= 20, f"Score {score} deveria ser <= 20 sem docs"

    def test_permanence_with_high_buffer(self):
        project = _make_project(
            buffer_pool_percentage=25.0,
            start_date=date(2010, 1, 1),
            end_date=date(2050, 12, 31),
        )
        score = _score_permanence(project, 30)
        assert score >= 60, f"Score {score} deveria ser >= 60 com buffer alto"

    def test_permanence_without_buffer(self):
        project = _make_project(
            buffer_pool_percentage=None,
            project_type="REDD+",
            start_date=None,
            end_date=None,
        )
        score = _score_permanence(project, 30)
        assert score <= 25, f"Score {score} deveria ser <= 25 sem buffer"

    def test_mrv_with_quarterly_monitoring(self):
        project = _make_project(monitoring_frequency="Quarterly", methodology="VM0015")
        score = _score_mrv(project, 35)
        assert score >= 70, f"Score {score} deveria ser >= 70 com monitoramento trimestral"

    def test_mrv_without_monitoring(self):
        project = _make_project(monitoring_frequency=None, methodology=None)
        score = _score_mrv(project, 35)
        assert score <= 15, f"Score {score} deveria ser <= 15 sem monitoramento"

    def test_governance_with_registry(self):
        project = _make_project(proponent="Corp", registry="Gold Standard", external_id="GS-001", methodology="M1")
        score = _score_governance(project, 30)
        assert score >= 55, f"Score {score} deveria ser >= 55 com governança completa"

    def test_governance_without_registry(self):
        project = _make_project(proponent=None, registry=None, external_id=None, methodology=None)
        score = _score_governance(project, 30)
        assert score <= 10, f"Score {score} deveria ser <= 10 sem governança"

    def test_co_benefits_developing_country(self):
        project = _make_project(country="Brazil", description="x" * 300)
        score = _score_co_benefits(project, 45)
        assert score >= 60, f"Score {score} deveria ser >= 60 em país em desenvolvimento"

    def test_baseline_integrity_with_docs(self):
        project = _make_project(
            baseline_scenario="x" * 500,
            total_credits_issued=100000,
            area_hectares=50000,
            methodology="VM0015",
        )
        score = _score_baseline_integrity(project, 35)
        assert score >= 60, f"Score {score} deveria ser >= 60 com baseline documentado"

    def test_baseline_integrity_overcrediting(self):
        project = _make_project(
            baseline_scenario=None,
            total_credits_issued=1000000,
            area_hectares=1000,
            methodology=None,
        )
        score = _score_baseline_integrity(project, 35)
        assert score <= 10, f"Score {score} deveria ser <= 10 com overcrediting"

    def test_scores_clamped_0_100(self):
        """Verifica que scores ficam entre 0 e 100."""
        project_good = _make_project(
            additionality_justification="x" * 1000,
            methodology="VM0015",
        )
        score = _score_additionality(project_good, 80)
        assert 0 <= score <= 100

        project_bad = _make_project(
            additionality_justification=None,
            methodology=None,
        )
        score = _score_additionality(project_bad, 5)
        assert 0 <= score <= 100


class TestCalculateRating:
    """Testa o cálculo completo de rating."""

    def test_good_project_high_score(self):
        """Projeto com documentação completa deve ter score alto."""
        project = _make_project()
        rating = calculate_rating(project)
        assert rating.overall_score >= 60, f"Score {rating.overall_score} deveria ser >= 60"
        assert rating.grade in (RatingGrade.BBB, RatingGrade.A, RatingGrade.AA, RatingGrade.AAA)

    def test_bad_project_low_score(self):
        """Projeto sem documentação deve ter score baixo."""
        project = _make_project(
            methodology=None,
            baseline_scenario=None,
            additionality_justification=None,
            monitoring_frequency=None,
            buffer_pool_percentage=None,
            proponent=None,
            external_id=None,
            description=None,
            registry=None,
            start_date=None,
            end_date=None,
            project_type="Other",
        )
        rating = calculate_rating(project)
        assert rating.overall_score < 40, f"Score {rating.overall_score} deveria ser < 40"
        assert rating.grade in (RatingGrade.D, RatingGrade.C, RatingGrade.CC, RatingGrade.CCC, RatingGrade.B)

    def test_medium_project_medium_score(self):
        """Projeto com documentação parcial deve ter score mediano."""
        project = _make_project(
            methodology="VM0015",
            baseline_scenario=None,
            additionality_justification="Short justification",
            monitoring_frequency="Annual",
            buffer_pool_percentage=5.0,
            proponent="Corp",
            external_id=None,
            description="Short desc",
            project_type="REDD+",
            start_date=date(2020, 1, 1),
            end_date=date(2035, 12, 31),
        )
        rating = calculate_rating(project)
        assert 35 <= rating.overall_score <= 65, f"Score {rating.overall_score} deveria estar entre 35-65"

    def test_rating_has_all_fields(self):
        """Verifica que o rating retorna todos os campos necessários."""
        project = _make_project()
        rating = calculate_rating(project)
        assert rating.project_id == 1
        assert 0 <= rating.overall_score <= 100
        assert rating.grade is not None
        assert 0 <= rating.additionality_score <= 100
        assert 0 <= rating.permanence_score <= 100
        assert 0 <= rating.leakage_score <= 100
        assert 0 <= rating.mrv_score <= 100
        assert 0 <= rating.co_benefits_score <= 100
        assert 0 <= rating.governance_score <= 100
        assert 0 <= rating.baseline_integrity_score <= 100
        assert 0 <= rating.confidence_level <= 1
        assert isinstance(rating.explanation, str)
        assert isinstance(rating.risk_flags, list)

    def test_confidence_level_full_data(self):
        """Projeto com dados completos deve ter confiança alta."""
        project = _make_project()
        rating = calculate_rating(project)
        assert rating.confidence_level >= 0.8

    def test_confidence_level_sparse_data(self):
        """Projeto com poucos dados deve ter confiança baixa."""
        project = _make_project(
            methodology=None, baseline_scenario=None,
            additionality_justification=None, monitoring_frequency=None,
            buffer_pool_percentage=None, proponent=None,
            external_id=None, description=None,
        )
        rating = calculate_rating(project)
        assert rating.confidence_level <= 0.3

    def test_risk_flags_bad_project(self):
        """Projeto ruim deve gerar flags de risco."""
        project = _make_project(
            methodology=None, baseline_scenario=None,
            additionality_justification=None, monitoring_frequency=None,
            buffer_pool_percentage=None, proponent=None,
            external_id=None, description=None, registry=None,
            project_type="Other",
        )
        rating = calculate_rating(project)
        assert len(rating.risk_flags) > 0, "Projeto ruim deveria ter flags de risco"

    def test_explanation_contains_project_name(self):
        """Explicação deve conter o nome do projeto."""
        project = _make_project(name="Amazon REDD+ Project")
        rating = calculate_rating(project)
        assert "Amazon REDD+ Project" in rating.explanation
