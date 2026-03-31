"""
Testes unitários para o Portfolio Analytics Engine v5.
Verifica métricas, recomendações deduplicadas, flags de risco, motivos e paginação por aba.
"""
import pytest
from app.services.portfolio_analytics import (
    _generate_recommendations as generate_recommendations,
    _generate_risk_flag_summary,
    _generate_reasons,
    group_recommendations_by_action,
)


def _make_positions(scores, project_types=None, countries=None):
    """Cria posições de portfólio agregadas por projeto (sem duplicação)."""
    positions = []
    for i, score in enumerate(scores):
        grade = "A" if score >= 70 else "BBB" if score >= 60 else "BB" if score >= 50 else "B" if score >= 40 else "CCC"
        ptype = project_types[i] if project_types and i < len(project_types) else "REDD+"
        country = countries[i] if countries and i < len(countries) else "Brazil"
        risk_flags = []
        if score < 40:
            risk_flags = [
                {"type": "permanence_risk", "severity": "high", "message": "Alto risco de reversão"},
                {"type": "leakage_risk", "severity": "high", "message": "Risco de vazamento"},
            ]
        elif score < 60:
            risk_flags = [
                {"type": "permanence_risk", "severity": "medium", "message": "Risco moderado de reversão"},
            ]
        positions.append({
            "project_id": i + 1,
            "project_name": f"Project {i + 1}",
            "project_type": ptype,
            "country": country,
            "registry": "Verra",
            "total_quantity": 10000,
            "total_value": 100000,
            "score": score,
            "grade": grade,
            "risk_flags": risk_flags,
            "num_positions": 2,
            "avg_price_eur": 10.0,
        })
    return positions


class TestGenerateRecommendations:
    """Testa geração de recomendações de rebalanceamento deduplicadas."""

    def test_sell_recommendations_for_low_scores(self):
        """Projetos com score < 40 devem gerar recomendação de venda."""
        positions = _make_positions([20, 30, 35, 70, 80])
        type_dist = {"REDD+": 50000}
        country_dist = {"Brazil": 50000}
        avg_score = sum(p['score'] for p in positions) / len(positions)
        recs = generate_recommendations(positions, avg_score, type_dist, country_dist)
        sell_recs = [r for r in recs if r["action"] == "sell"]
        assert len(sell_recs) == 3, f"Deveria ter 3 sell, tem {len(sell_recs)}"

    def test_rebalance_recommendations_for_medium_scores(self):
        """Projetos com score 40-60 devem gerar recomendação de rebalanceamento."""
        positions = _make_positions([45, 50, 55, 70, 80])
        type_dist = {"REDD+": 50000}
        country_dist = {"Brazil": 50000}
        avg_score = sum(p['score'] for p in positions) / len(positions)
        recs = generate_recommendations(positions, avg_score, type_dist, country_dist)
        rebalance_recs = [r for r in recs if r["action"] == "rebalance" and r["project_id"] is not None]
        assert len(rebalance_recs) == 3, f"Deveria ter 3 rebalance, tem {len(rebalance_recs)}"

    def test_hold_recommendations_for_high_scores(self):
        """Projetos com score >= 60 devem gerar recomendação de manter."""
        positions = _make_positions([65, 70, 80, 90])
        type_dist = {"REDD+": 40000}
        country_dist = {"Brazil": 40000}
        avg_score = sum(p['score'] for p in positions) / len(positions)
        recs = generate_recommendations(positions, avg_score, type_dist, country_dist)
        hold_recs = [r for r in recs if r["action"] == "hold"]
        assert len(hold_recs) == 4, f"Deveria ter 4 hold, tem {len(hold_recs)}"

    def test_no_duplicate_project_ids(self):
        """Cada projeto deve aparecer apenas uma vez nas recomendações."""
        positions = _make_positions([20, 50, 80])
        avg_score = 50
        recs = generate_recommendations(positions, avg_score, {"REDD+": 30000}, {"Brazil": 30000})
        project_ids = [r["project_id"] for r in recs if r["project_id"] is not None]
        assert len(project_ids) == len(set(project_ids)), "Não deveria haver project_ids duplicados"

    def test_recommendations_have_risk_flags(self):
        """Recomendações de sell devem incluir risk_flags."""
        positions = _make_positions([20, 30])
        avg_score = 25
        recs = generate_recommendations(positions, avg_score, {"REDD+": 20000}, {"Brazil": 20000})
        sell_recs = [r for r in recs if r["action"] == "sell"]
        for rec in sell_recs:
            assert "risk_flags" in rec, "Recomendação deve ter risk_flags"
            assert isinstance(rec["risk_flags"], list)
            assert len(rec["risk_flags"]) > 0, "Sell recs devem ter flags de risco"

    def test_recommendations_have_reasons(self):
        """Todas as recomendações devem incluir lista de motivos."""
        positions = _make_positions([20, 50, 80])
        avg_score = 50
        recs = generate_recommendations(positions, avg_score, {"REDD+": 30000}, {"Brazil": 30000})
        for rec in recs:
            assert "reasons" in rec, "Recomendação deve ter reasons"
            assert isinstance(rec["reasons"], list)
            assert len(rec["reasons"]) > 0, f"Recomendação '{rec['project_name']}' deve ter pelo menos 1 motivo"

    def test_recommendations_have_all_fields(self):
        """Cada recomendação deve ter todos os campos obrigatórios."""
        positions = _make_positions([30, 50, 80])
        avg_score = 53
        recs = generate_recommendations(positions, avg_score, {"REDD+": 30000}, {"Brazil": 30000})
        required_fields = {
            "project_id", "project_name", "project_type", "country", "registry",
            "current_grade", "current_score", "total_quantity", "total_value",
            "action", "reason", "reasons", "risk_flags", "risk_level", "priority"
        }
        for rec in recs:
            for field in required_fields:
                assert field in rec, f"Campo '{field}' faltando na recomendação"

    def test_concentration_alert_type(self):
        """Concentração > 30% em um tipo deve gerar rebalance."""
        positions = _make_positions([70, 70])
        type_dist = {"REDD+": 8000, "ARR": 2000}  # 80% REDD+
        country_dist = {"Brazil": 10000}
        avg_score = 70
        recs = generate_recommendations(positions, avg_score, type_dist, country_dist)
        type_recs = [r for r in recs if r["action"] == "rebalance" and "Concentração" in r["project_name"]]
        assert len(type_recs) >= 1, "Deveria alertar sobre concentração"

    def test_concentration_alert_country(self):
        """Concentração > 20% em um país deve gerar rebalance."""
        positions = _make_positions([70, 70])
        type_dist = {"REDD+": 10000}
        country_dist = {"Brazil": 8000, "India": 2000}  # 80% Brazil
        avg_score = 70
        recs = generate_recommendations(positions, avg_score, type_dist, country_dist)
        country_recs = [r for r in recs if r["action"] == "rebalance" and "Concentração" in r["project_name"]]
        assert len(country_recs) >= 1, "Deveria alertar sobre concentração geográfica"

    def test_empty_positions(self):
        """Sem posições, não deve gerar recomendações."""
        recs = generate_recommendations([], 0, {}, {})
        assert len(recs) == 0

    def test_recommendations_have_priority(self):
        """Cada recomendação deve ter prioridade definida."""
        positions = _make_positions([20, 50, 80])
        avg_score = 50
        recs = generate_recommendations(positions, avg_score, {"REDD+": 30000}, {"Brazil": 30000})
        for rec in recs:
            assert "priority" in rec
            assert isinstance(rec["priority"], int)
            assert rec["priority"] > 0


class TestRiskFlagSummary:
    """Testa geração de resumo de flags de risco."""

    def test_empty_flags(self):
        result = _generate_risk_flag_summary([])
        assert result == []

    def test_flags_preserved(self):
        flags = [
            {"type": "permanence_risk", "severity": "high", "message": "Alto risco"},
            {"type": "leakage_risk", "severity": "medium", "message": "Risco moderado"},
        ]
        result = _generate_risk_flag_summary(flags)
        assert len(result) == 2
        assert result[0]["type"] == "permanence_risk"
        assert result[0]["severity"] == "high"

    def test_missing_fields_handled(self):
        flags = [{"type": "test"}]
        result = _generate_risk_flag_summary(flags)
        assert len(result) == 1
        assert result[0]["severity"] == "medium"  # default


class TestGenerateReasons:
    """Testa geração de motivos detalhados."""

    def test_sell_reasons(self):
        project = {"score": 20, "grade": "CC", "risk_flags": [
            {"severity": "high", "message": "Alto risco"}
        ], "total_quantity": 15000, "registry": "Verra"}
        reasons = _generate_reasons(project, "sell", 50)
        assert len(reasons) >= 2
        assert any("muito baixo" in r.lower() for r in reasons)

    def test_rebalance_reasons(self):
        project = {"score": 45, "grade": "B", "risk_flags": [
            {"severity": "medium", "message": "Risco moderado"}
        ], "total_quantity": 10000, "registry": "Verra"}
        reasons = _generate_reasons(project, "rebalance", 60)
        assert len(reasons) >= 1
        assert any("mediano" in r.lower() or "flag" in r.lower() for r in reasons)

    def test_hold_reasons(self):
        project = {"score": 85, "grade": "AA", "risk_flags": [], "total_quantity": 10000, "registry": "Verra"}
        reasons = _generate_reasons(project, "hold", 60)
        assert len(reasons) >= 1
        assert any("sólido" in r.lower() or "qualidade" in r.lower() for r in reasons)


class TestGroupRecommendations:
    """Testa agrupamento de recomendações por ação com paginação."""

    def test_group_by_action(self):
        """Recomendações devem ser agrupadas por ação com metadados de paginação."""
        recs = [
            {"action": "sell", "project_name": "P1", "priority": 1},
            {"action": "sell", "project_name": "P2", "priority": 2},
            {"action": "rebalance", "project_name": "P3", "priority": 3},
            {"action": "hold", "project_name": "P4", "priority": 4},
            {"action": "hold", "project_name": "P5", "priority": 5},
            {"action": "hold", "project_name": "P6", "priority": 6},
        ]
        grouped = group_recommendations_by_action(recs)
        assert "sell" in grouped
        assert "rebalance" in grouped
        assert "hold" in grouped
        # Cada grupo agora tem estrutura paginada
        assert grouped["sell"]["total"] == 2
        assert grouped["rebalance"]["total"] == 1
        assert grouped["hold"]["total"] == 3
        assert len(grouped["sell"]["items"]) == 2
        assert len(grouped["hold"]["items"]) == 3

    def test_pagination_metadata(self):
        """Cada grupo deve ter metadados de paginação."""
        recs = [{"action": "sell", "project_name": f"P{i}", "priority": i} for i in range(25)]
        grouped = group_recommendations_by_action(recs, page=1, page_size=10)
        sell = grouped["sell"]
        assert sell["total"] == 25
        assert sell["page"] == 1
        assert sell["page_size"] == 10
        assert sell["total_pages"] == 3
        assert len(sell["items"]) == 10

    def test_pagination_page_2(self):
        """Página 2 deve retornar os itens corretos."""
        recs = [{"action": "sell", "project_name": f"P{i}", "priority": i} for i in range(25)]
        grouped = group_recommendations_by_action(recs, page=2, page_size=10)
        sell = grouped["sell"]
        assert sell["page"] == 2
        assert len(sell["items"]) == 10

    def test_pagination_last_page(self):
        """Última página deve retornar itens restantes."""
        recs = [{"action": "sell", "project_name": f"P{i}", "priority": i} for i in range(25)]
        grouped = group_recommendations_by_action(recs, page=3, page_size=10)
        sell = grouped["sell"]
        assert sell["page"] == 3
        assert len(sell["items"]) == 5

    def test_group_sorted_by_priority(self):
        """Cada grupo deve estar ordenado por prioridade."""
        recs = [
            {"action": "sell", "project_name": "P2", "priority": 5},
            {"action": "sell", "project_name": "P1", "priority": 1},
            {"action": "sell", "project_name": "P3", "priority": 3},
        ]
        grouped = group_recommendations_by_action(recs)
        priorities = [r["priority"] for r in grouped["sell"]["items"]]
        assert priorities == sorted(priorities), "Deveria estar ordenado por prioridade"

    def test_empty_recommendations(self):
        """Lista vazia deve retornar dict vazio."""
        grouped = group_recommendations_by_action([])
        assert grouped == {}

    def test_single_action_type(self):
        """Apenas um tipo de ação deve gerar apenas uma chave."""
        recs = [
            {"action": "hold", "project_name": "P1", "priority": 1},
            {"action": "hold", "project_name": "P2", "priority": 2},
        ]
        grouped = group_recommendations_by_action(recs)
        assert len(grouped) == 1
        assert "hold" in grouped
        assert grouped["hold"]["total"] == 2
