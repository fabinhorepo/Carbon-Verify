"""
Testes unitários para o Portfolio Analytics Engine.
Verifica métricas, recomendações e agrupamento por ação.
"""
import pytest
from app.services.portfolio_analytics import (
    _generate_recommendations as generate_recommendations,
    group_recommendations_by_action,
)


def _make_positions(scores):
    """Cria posições de portfólio com scores específicos."""
    positions = []
    for i, score in enumerate(scores):
        grade = "A" if score >= 70 else "BBB" if score >= 60 else "BB" if score >= 50 else "B" if score >= 40 else "CCC"
        positions.append({
            "position_id": i + 1,
            "project_id": i + 1,
            "project_name": f"Project {i + 1}",
            "project_type": "REDD+",
            "country": "Brazil",
            "grade": grade,
            "score": score,
            "quantity": 10000,
            "price_usd": 10.0,
        })
    return positions


class TestGenerateRecommendations:
    """Testa geração de recomendações de rebalanceamento."""

    def test_sell_recommendations_for_low_scores(self):
        """Projetos com score < 40 devem gerar recomendação de venda."""
        positions = _make_positions([20, 30, 35, 70, 80])
        type_dist = {"REDD+": 5}
        country_dist = {"Brazil": 5}
        avg_score = sum(p['score'] for p in positions) / len(positions) if positions else 0
        recs = generate_recommendations(positions, avg_score, type_dist, country_dist)
        sell_recs = [r for r in recs if r["action"] == "sell"]
        assert len(sell_recs) == 3, f"Deveria ter 3 sell, tem {len(sell_recs)}"

    def test_rebalance_recommendations_for_medium_scores(self):
        """Projetos com score 40-60 devem gerar recomendação de rebalanceamento."""
        positions = _make_positions([45, 50, 55, 70, 80])
        type_dist = {"REDD+": 5}
        country_dist = {"Brazil": 5}
        avg_score = sum(p['score'] for p in positions) / len(positions) if positions else 0
        recs = generate_recommendations(positions, avg_score, type_dist, country_dist)
        rebalance_recs = [r for r in recs if r["action"] == "rebalance" and r["project_id"] is not None]
        assert len(rebalance_recs) == 3, f"Deveria ter 3 rebalance, tem {len(rebalance_recs)}"

    def test_hold_recommendations_for_high_scores(self):
        """Projetos com score >= 60 devem gerar recomendação de manter."""
        positions = _make_positions([65, 70, 80, 90])
        type_dist = {"REDD+": 4}
        country_dist = {"Brazil": 4}
        avg_score = sum(p['score'] for p in positions) / len(positions) if positions else 0
        recs = generate_recommendations(positions, avg_score, type_dist, country_dist)
        hold_recs = [r for r in recs if r["action"] == "hold"]
        assert len(hold_recs) == 4, f"Deveria ter 4 hold, tem {len(hold_recs)}"

    def test_concentration_alert_type(self):
        """Concentração > 30% em um tipo deve gerar rebalance."""
        positions = _make_positions([70, 70])
        type_dist = {"REDD+": 8, "ARR": 2}  # 80% REDD+
        country_dist = {"Brazil": 10}
        avg_score = sum(p['score'] for p in positions) / len(positions) if positions else 0
        recs = generate_recommendations(positions, avg_score, type_dist, country_dist)
        type_recs = [r for r in recs if r["action"] == "rebalance" and "Tipo:" in r["project_name"]]
        assert len(type_recs) >= 1, "Deveria alertar sobre concentração de tipo"

    def test_concentration_alert_country(self):
        """Concentração > 20% em um país deve gerar rebalance."""
        positions = _make_positions([70, 70])
        type_dist = {"REDD+": 10}
        country_dist = {"Brazil": 8, "India": 2}  # 80% Brazil
        avg_score = sum(p['score'] for p in positions) / len(positions) if positions else 0
        recs = generate_recommendations(positions, avg_score, type_dist, country_dist)
        country_recs = [r for r in recs if r["action"] == "rebalance" and "País:" in r["project_name"]]
        assert len(country_recs) >= 1, "Deveria alertar sobre concentração geográfica"

    def test_recommendations_have_priority(self):
        """Cada recomendação deve ter prioridade definida."""
        positions = _make_positions([20, 50, 80])
        type_dist = {"REDD+": 3}
        country_dist = {"Brazil": 3}
        avg_score = sum(p['score'] for p in positions) / len(positions) if positions else 0
        recs = generate_recommendations(positions, avg_score, type_dist, country_dist)
        for rec in recs:
            assert "priority" in rec
            assert isinstance(rec["priority"], int)
            assert rec["priority"] > 0

    def test_empty_positions(self):
        """Sem posições, não deve gerar recomendações de projetos."""
        recs = generate_recommendations([], 0, {}, {})
        assert len(recs) == 0

    def test_all_recommendation_fields(self):
        """Cada recomendação deve ter todos os campos obrigatórios."""
        positions = _make_positions([30, 50, 80])
        avg_score = sum(p['score'] for p in positions) / len(positions)
        recs = generate_recommendations(positions, avg_score, {"REDD+": 3}, {"Brazil": 3})
        required_fields = {"project_id", "project_name", "current_grade", "current_score", "action", "reason", "risk_level", "priority"}
        for rec in recs:
            for field in required_fields:
                assert field in rec, f"Campo '{field}' faltando na recomendação"


class TestGroupRecommendations:
    """Testa agrupamento de recomendações por ação."""

    def test_group_by_action(self):
        """Recomendações devem ser agrupadas por ação."""
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
        assert len(grouped["sell"]) == 2
        assert len(grouped["rebalance"]) == 1
        assert len(grouped["hold"]) == 3

    def test_group_sorted_by_priority(self):
        """Cada grupo deve estar ordenado por prioridade."""
        recs = [
            {"action": "sell", "project_name": "P2", "priority": 5},
            {"action": "sell", "project_name": "P1", "priority": 1},
            {"action": "sell", "project_name": "P3", "priority": 3},
        ]
        grouped = group_recommendations_by_action(recs)
        priorities = [r["priority"] for r in grouped["sell"]]
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
