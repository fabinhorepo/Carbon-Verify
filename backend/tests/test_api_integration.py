"""
Testes de integração para a API Carbon Verify v6.
Testa endpoints completos com banco de dados real e autenticação.
300 projetos (150 Verra + 150 Gold Standard), distribuição 50/35/15.
Inclui testes para: risk-matrix tabular, fraud-alerts agrupados por tipo,
paginação, ordenação, recomendações com flags de risco.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from main import app


@pytest_asyncio.fixture(scope="module")
async def client():
    """Cria um client HTTP assíncrono para testes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="module")
async def auth_token(client):
    """Obtém token JWT para testes autenticados."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "demo@carbonverify.com",
        "password": "demo123",
    })
    assert response.status_code == 200, f"Login falhou: {response.text}"
    return response.json()["access_token"]


# ============================================================
# Health Check
# ============================================================
class TestHealthEndpoint:

    @pytest.mark.asyncio
    async def test_health(self, client):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Carbon Verify"


# ============================================================
# Autenticação
# ============================================================
class TestAuthEndpoints:

    @pytest.mark.asyncio
    async def test_login_success(self, client):
        response = await client.post("/api/v1/auth/login", json={
            "email": "demo@carbonverify.com",
            "password": "demo123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
        response = await client.post("/api/v1/auth/login", json={
            "email": "demo@carbonverify.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        response = await client.post("/api/v1/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "test123",
        })
        assert response.status_code == 401


# ============================================================
# Projetos (com paginação e ordenação) - 300 projetos
# ============================================================
class TestProjectsEndpoints:

    @pytest.mark.asyncio
    async def test_list_projects_default(self, client):
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

    @pytest.mark.asyncio
    async def test_list_projects_300_total(self, client):
        response = await client.get("/api/v1/projects?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 300, f"Deveria ter 300 projetos, tem {data['total']}"

    @pytest.mark.asyncio
    async def test_pagination_20_per_page(self, client):
        response = await client.get("/api/v1/projects?page=1&page_size=20")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 20
        assert data["page_size"] == 20
        assert data["total_pages"] == 15  # 300 / 20

    @pytest.mark.asyncio
    async def test_pagination_page_2(self, client):
        response = await client.get("/api/v1/projects?page=2&page_size=20")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert len(data["items"]) == 20

    @pytest.mark.asyncio
    async def test_filter_by_registry_verra(self, client):
        response = await client.get("/api/v1/projects?registry=Verra")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 150, f"Deveria ter 150 Verra, tem {data['total']}"
        for item in data["items"]:
            assert item["registry"] == "Verra"

    @pytest.mark.asyncio
    async def test_filter_by_registry_gold_standard(self, client):
        response = await client.get("/api/v1/projects?registry=Gold Standard")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 150, f"Deveria ter 150 GS, tem {data['total']}"
        for item in data["items"]:
            assert item["registry"] == "Gold Standard"

    @pytest.mark.asyncio
    async def test_project_detail(self, client):
        response = await client.get("/api/v1/projects/1")
        assert response.status_code == 200
        data = response.json()
        if "project" in data:
            assert data["project"]["id"] == 1
        else:
            assert data["id"] == 1

    @pytest.mark.asyncio
    async def test_project_detail_not_found(self, client):
        response = await client.get("/api/v1/projects/9999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_project_rating_has_all_dimensions(self, client):
        response = await client.get("/api/v1/projects/1")
        data = response.json()
        rating = data.get("rating", data)
        required_fields = [
            "overall_score", "grade",
            "additionality_score", "permanence_score", "leakage_score",
            "mrv_score", "co_benefits_score", "governance_score",
            "baseline_integrity_score", "confidence_level", "explanation",
        ]
        for field in required_fields:
            assert field in rating, f"Campo '{field}' faltando no rating"


# ============================================================
# Fraud Alerts - Paginação padrão
# ============================================================
class TestFraudAlertsEndpoints:

    @pytest.mark.asyncio
    async def test_list_fraud_alerts(self, client):
        response = await client.get("/api/v1/fraud-alerts")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] > 0

    @pytest.mark.asyncio
    async def test_fraud_alerts_pagination(self, client):
        response = await client.get("/api/v1/fraud-alerts?page=1&page_size=20")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 20
        assert data["page_size"] == 20

    @pytest.mark.asyncio
    async def test_fraud_alerts_filter_severity(self, client):
        response = await client.get("/api/v1/fraud-alerts?severity=high")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["severity"] == "high"

    @pytest.mark.asyncio
    async def test_fraud_alert_structure(self, client):
        response = await client.get("/api/v1/fraud-alerts?page=1&page_size=1")
        data = response.json()
        if data["items"]:
            alert = data["items"][0]
            required = ["id", "alert_type", "severity", "title", "description"]
            for field in required:
                assert field in alert, f"Campo '{field}' faltando no alerta"


# ============================================================
# Fraud Alerts - Agrupados por Tipo (NOVO)
# ============================================================
class TestFraudAlertsGroupedByType:

    @pytest.mark.asyncio
    async def test_grouped_summary(self, client):
        """Deve retornar resumo com todos os 6 tipos de fraude."""
        response = await client.get("/api/v1/fraud-alerts/grouped-by-type")
        assert response.status_code == 200
        data = response.json()
        assert "total_alerts" in data
        assert "types" in data
        assert data["total_alerts"] > 0
        expected_types = [
            "overcrediting", "missing_area", "vintage_age",
            "governance_gaps", "insufficient_buffer", "retirement_anomaly",
        ]
        for t in expected_types:
            assert t in data["types"], f"Tipo '{t}' deveria estar presente"

    @pytest.mark.asyncio
    async def test_grouped_type_has_explanation(self, client):
        """Cada tipo deve ter explicações para leigos."""
        response = await client.get("/api/v1/fraud-alerts/grouped-by-type")
        data = response.json()
        for type_key, type_data in data["types"].items():
            # Explicações podem estar em type_data.explanation ou diretamente
            explanation = type_data.get("explanation", type_data)
            assert "what_is" in explanation, f"Tipo '{type_key}' deve ter 'what_is'"
            assert "consequences" in explanation, f"Tipo '{type_key}' deve ter 'consequences'"
            assert "ideal_situation" in explanation, f"Tipo '{type_key}' deve ter 'ideal_situation'"
            assert "total" in type_data or "items" in type_data, f"Tipo '{type_key}' deve ter 'total' ou 'items'"
            assert len(explanation["what_is"]) > 20, f"Explicação de '{type_key}' muito curta"

    @pytest.mark.asyncio
    async def test_grouped_type_paginated(self, client):
        """Endpoint de tipo específico deve retornar paginação de 10."""
        response = await client.get(
            "/api/v1/fraud-alerts/grouped-by-type/overcrediting?page=1&page_size=10"
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert data["page_size"] == 10
        assert len(data["items"]) <= 10

    @pytest.mark.asyncio
    async def test_grouped_type_page_2(self, client):
        """Deve retornar página 2 de um tipo com muitos alertas."""
        response = await client.get(
            "/api/v1/fraud-alerts/grouped-by-type/overcrediting?page=2&page_size=10"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert len(data["items"]) <= 10

    @pytest.mark.asyncio
    async def test_grouped_type_invalid_returns_error(self, client):
        """Tipo inválido deve retornar 404 ou lista vazia."""
        response = await client.get(
            "/api/v1/fraud-alerts/grouped-by-type/nonexistent_type?page=1&page_size=10"
        )
        # Aceita 404 ou 200 com total=0
        if response.status_code == 200:
            data = response.json()
            assert data["total"] == 0
        else:
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_grouped_overcrediting_has_alerts(self, client):
        """Overcrediting deve ter alertas (é o tipo mais comum)."""
        response = await client.get(
            "/api/v1/fraud-alerts/grouped-by-type/overcrediting?page=1&page_size=10"
        )
        data = response.json()
        assert data["total"] > 0, "Overcrediting deveria ter alertas"
        for item in data["items"]:
            assert item["alert_type"] == "overcrediting"

    @pytest.mark.asyncio
    async def test_fraud_summary(self, client):
        """Endpoint de resumo deve funcionar."""
        response = await client.get("/api/v1/fraud-alerts/summary")
        assert response.status_code == 200
        data = response.json()
        assert "by_severity" in data
        assert "by_type" in data
        # Total pode estar em 'total' ou calculado a partir de by_severity
        total = data.get("total", sum(data["by_severity"].values()))
        assert total > 0, "Deveria ter alertas"


# ============================================================
# Portfólio (com autenticação)
# ============================================================
class TestPortfolioEndpoints:

    @pytest.mark.asyncio
    async def test_list_portfolios_unauthorized(self, client):
        response = await client.get("/api/v1/portfolios")
        assert response.status_code in (401, 403), f"Esperado 401 ou 403, recebeu {response.status_code}"

    @pytest.mark.asyncio
    async def test_list_portfolios(self, client, auth_token):
        response = await client.get(
            "/api/v1/portfolios",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_portfolio_detail_with_pagination(self, client, auth_token):
        response = await client.get(
            "/api/v1/portfolios/1?page=1&page_size=20",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "portfolio" in data
        assert "metrics" in data
        metrics = data["metrics"]
        assert "positions_pagination" in metrics
        assert metrics["positions_pagination"]["page_size"] == 20

    @pytest.mark.asyncio
    async def test_portfolio_positions_total(self, client, auth_token):
        """300 projetos x 2 créditos = 600 posições."""
        response = await client.get(
            "/api/v1/portfolios/1?page=1&page_size=20",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        total_positions = data["metrics"]["positions_pagination"]["total"]
        assert total_positions == 600, f"Deveria ter 600 posições, tem {total_positions}"

    @pytest.mark.asyncio
    async def test_portfolio_recommendations_grouped(self, client, auth_token):
        response = await client.get(
            "/api/v1/portfolios/1?page=1&rec_page=1&rec_page_size=20",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        metrics = data["metrics"]
        assert "recommendations_grouped" in metrics
        grouped = metrics["recommendations_grouped"]
        assert isinstance(grouped, dict)
        assert "sell" in grouped, "Deveria ter recomendações de venda"
        assert "hold" in grouped, "Deveria ter recomendações de manter"
        assert "rebalance" in grouped, "Deveria ter recomendações de rebalanceamento"

    @pytest.mark.asyncio
    async def test_recommendations_have_pagination(self, client, auth_token):
        """Cada aba de recomendações deve ter metadados de paginação."""
        response = await client.get(
            "/api/v1/portfolios/1?page=1&rec_page=1&rec_page_size=20",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        grouped = data["metrics"]["recommendations_grouped"]
        for action, tab_data in grouped.items():
            assert "items" in tab_data, f"Aba '{action}' deve ter 'items'"
            assert "total" in tab_data, f"Aba '{action}' deve ter 'total'"
            assert "page" in tab_data, f"Aba '{action}' deve ter 'page'"
            assert "page_size" in tab_data, f"Aba '{action}' deve ter 'page_size'"
            assert "total_pages" in tab_data, f"Aba '{action}' deve ter 'total_pages'"

    @pytest.mark.asyncio
    async def test_recommendations_no_duplicates(self, client, auth_token):
        """Não deve haver project_ids duplicados nas recomendações."""
        response = await client.get(
            "/api/v1/portfolios/1?page=1&rec_page=1&rec_page_size=100",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        total_recs = data["metrics"]["total_recommendations"]
        assert total_recs > 0, "Deveria ter recomendações"
        # Verificar que total_recs <= 300 + concentrações (sem duplicação)
        assert total_recs <= 320, f"Total {total_recs} parece ter duplicações (esperado <= 320)"

    @pytest.mark.asyncio
    async def test_recommendations_have_risk_flags(self, client, auth_token):
        """Recomendações de sell devem ter risk_flags."""
        response = await client.get(
            "/api/v1/portfolios/1?page=1&rec_page=1&rec_page_size=20",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        sell_items = data["metrics"]["recommendations_grouped"]["sell"]["items"]
        for item in sell_items:
            assert "risk_flags" in item, "Sell rec deve ter risk_flags"
            assert isinstance(item["risk_flags"], list)

    @pytest.mark.asyncio
    async def test_recommendations_have_reasons(self, client, auth_token):
        """Todas as recomendações devem ter lista de motivos."""
        response = await client.get(
            "/api/v1/portfolios/1?page=1&rec_page=1&rec_page_size=20",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        grouped = data["metrics"]["recommendations_grouped"]
        for action, tab_data in grouped.items():
            for item in tab_data["items"]:
                assert "reasons" in item, f"Rec em '{action}' deve ter reasons"
                assert isinstance(item["reasons"], list)
                assert len(item["reasons"]) > 0, f"Rec '{item['project_name']}' deve ter pelo menos 1 motivo"

    @pytest.mark.asyncio
    async def test_sell_count_matches_distribution(self, client, auth_token):
        """~15% dos projetos devem ser sell (score < 40)."""
        response = await client.get(
            "/api/v1/portfolios/1?page=1&rec_page=1&rec_page_size=100",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        sell_total = data["metrics"]["recommendations_grouped"]["sell"]["total"]
        assert 30 <= sell_total <= 60, f"Sell deveria ser ~45, é {sell_total}"


# ============================================================
# Dashboard (com autenticação)
# ============================================================
class TestDashboardEndpoints:

    @pytest.mark.asyncio
    async def test_dashboard_metrics(self, client, auth_token):
        response = await client.get(
            "/api/v1/dashboard/metrics",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_projects" in data
        assert data["total_projects"] == 300
        assert "avg_quality_score" in data
        assert "grade_distribution" in data
        assert "risk_summary" in data

    @pytest.mark.asyncio
    async def test_dashboard_score_distribution(self, client, auth_token):
        """Verifica distribuição 50/35/15 no dashboard."""
        response = await client.get(
            "/api/v1/dashboard/metrics",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        risk = data["risk_summary"]
        total = risk.get("high_risk", 0) + risk.get("medium_risk", 0) + risk.get("low_risk", 0)
        assert total == 300, f"Total deveria ser 300, é {total}"
        high_pct = risk.get("high_risk", 0) / total * 100
        medium_pct = risk.get("medium_risk", 0) / total * 100
        low_pct = risk.get("low_risk", 0) / total * 100
        assert high_pct >= 10, f"High risk {high_pct:.0f}% deveria ser >= 10%"
        assert medium_pct >= 25, f"Medium risk {medium_pct:.0f}% deveria ser >= 25%"
        assert low_pct >= 40, f"Low risk {low_pct:.0f}% deveria ser >= 40%"

    @pytest.mark.asyncio
    async def test_dashboard_unauthorized(self, client):
        response = await client.get("/api/v1/dashboard/metrics")
        assert response.status_code in (401, 403), f"Esperado 401 ou 403, recebeu {response.status_code}"


# ============================================================
# Risk Matrix - Formato Tabular (NOVO)
# ============================================================
class TestRiskMatrixTabular:

    @pytest.mark.asyncio
    async def test_risk_matrix_structure(self, client, auth_token):
        """Risk matrix deve retornar formato tabular com grid, quality_levels e risk_levels."""
        response = await client.get(
            "/api/v1/dashboard/risk-matrix",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "grid" in data, "Deve ter 'grid'"
        assert "quality_levels" in data, "Deve ter 'quality_levels'"
        assert "risk_levels" in data, "Deve ter 'risk_levels'"
        assert "total_projects" in data, "Deve ter 'total_projects'"

    @pytest.mark.asyncio
    async def test_risk_matrix_total_300(self, client, auth_token):
        """Total de projetos na matrix deve ser 300."""
        response = await client.get(
            "/api/v1/dashboard/risk-matrix",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        assert data["total_projects"] == 300

    @pytest.mark.asyncio
    async def test_risk_matrix_quality_levels(self, client, auth_token):
        """Deve ter 3 níveis de qualidade: high, medium, low."""
        response = await client.get(
            "/api/v1/dashboard/risk-matrix",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        quality_keys = [ql["key"] for ql in data["quality_levels"]]
        assert "high" in quality_keys
        assert "medium" in quality_keys
        assert "low" in quality_keys

    @pytest.mark.asyncio
    async def test_risk_matrix_risk_levels(self, client, auth_token):
        """Deve ter 4 níveis de risco: none, low, medium, high."""
        response = await client.get(
            "/api/v1/dashboard/risk-matrix",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        risk_keys = [rl["key"] for rl in data["risk_levels"]]
        assert "none" in risk_keys
        assert "low" in risk_keys
        assert "medium" in risk_keys
        assert "high" in risk_keys

    @pytest.mark.asyncio
    async def test_risk_matrix_grid_has_all_cells(self, client, auth_token):
        """Grid deve ter todas as combinações quality x risk."""
        response = await client.get(
            "/api/v1/dashboard/risk-matrix",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        grid = data["grid"]
        for q_key in ["high", "medium", "low"]:
            assert q_key in grid, f"Grid deve ter qualidade '{q_key}'"
            for r_key in ["none", "low", "medium", "high"]:
                assert r_key in grid[q_key], f"Grid[{q_key}] deve ter risco '{r_key}'"
                cell = grid[q_key][r_key]
                assert "count" in cell, f"Célula [{q_key}][{r_key}] deve ter 'count'"
                assert "projects" in cell, f"Célula [{q_key}][{r_key}] deve ter 'projects'"

    @pytest.mark.asyncio
    async def test_risk_matrix_sum_equals_300(self, client, auth_token):
        """Soma de todos os counts nas células deve ser 300."""
        response = await client.get(
            "/api/v1/dashboard/risk-matrix",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        grid = data["grid"]
        total = 0
        for q_key in ["high", "medium", "low"]:
            for r_key in ["none", "low", "medium", "high"]:
                total += grid[q_key][r_key]["count"]
        assert total == 300, f"Soma das células deveria ser 300, é {total}"

    @pytest.mark.asyncio
    async def test_risk_matrix_cell_projects_have_fields(self, client, auth_token):
        """Projetos nas células devem ter campos necessários."""
        response = await client.get(
            "/api/v1/dashboard/risk-matrix",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        grid = data["grid"]
        # Encontrar uma célula com projetos
        for q_key in ["high", "medium", "low"]:
            for r_key in ["none", "low", "medium", "high"]:
                projects = grid[q_key][r_key]["projects"]
                if projects:
                    p = projects[0]
                    assert "project_id" in p
                    assert "name" in p
                    assert "quality_score" in p
                    assert "grade" in p
                    return
        pytest.fail("Nenhuma célula com projetos encontrada")

    @pytest.mark.asyncio
    async def test_risk_matrix_unauthorized(self, client):
        response = await client.get("/api/v1/dashboard/risk-matrix")
        assert response.status_code in (401, 403)


# ============================================================
# Market / Cotação de Carbono (NOVO)
# ============================================================
class TestMarketEndpoints:

    @pytest.mark.asyncio
    async def test_carbon_price_endpoint(self, client):
        """Endpoint de cotação de carbono deve retornar preço em EUR."""
        response = await client.get("/api/v1/market/carbon-price")
        assert response.status_code == 200
        data = response.json()
        assert "price_eur" in data, "Deve ter 'price_eur'"
        assert "currency" in data, "Deve ter 'currency'"
        assert data["currency"] == "EUR"
        assert data["price_eur"] > 0, "Preço deve ser positivo"

    @pytest.mark.asyncio
    async def test_carbon_price_has_market_info(self, client):
        """Cotação deve incluir informações do mercado."""
        response = await client.get("/api/v1/market/carbon-price")
        data = response.json()
        assert "market" in data, "Deve ter 'market'"
        assert "instrument" in data, "Deve ter 'instrument'"
        assert "source" in data, "Deve ter 'source'"
        assert "timestamp" in data, "Deve ter 'timestamp'"
        assert "unit" in data, "Deve ter 'unit'"
        assert data["unit"] == "tCO2e"

    @pytest.mark.asyncio
    async def test_carbon_price_has_change(self, client):
        """Cotação deve incluir variação 24h."""
        response = await client.get("/api/v1/market/carbon-price")
        data = response.json()
        assert "change_24h" in data, "Deve ter 'change_24h'"
        assert "change_pct_24h" in data, "Deve ter 'change_pct_24h'"

    @pytest.mark.asyncio
    async def test_market_summary(self, client):
        """Endpoint de resumo de mercado deve funcionar."""
        response = await client.get("/api/v1/market/summary")
        assert response.status_code == 200
        data = response.json()
        assert "eu_ets" in data, "Deve ter 'eu_ets'"
        assert data["eu_ets"]["currency"] == "EUR"


# ============================================================
# Fraud Alerts - project_name presente (NOVO)
# ============================================================
class TestFraudAlertsProjectName:

    @pytest.mark.asyncio
    async def test_fraud_alerts_have_project_name(self, client):
        """Alertas de fraude devem incluir project_name."""
        response = await client.get("/api/v1/fraud-alerts?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        for alert in data["items"]:
            assert "project_name" in alert, f"Alerta {alert['id']} deve ter 'project_name'"
            assert alert["project_name"] is not None, f"project_name do alerta {alert['id']} não deve ser None"
            assert len(alert["project_name"]) > 0, f"project_name do alerta {alert['id']} não deve ser vazio"

    @pytest.mark.asyncio
    async def test_grouped_alerts_have_project_name(self, client):
        """Alertas agrupados por tipo devem incluir project_name."""
        response = await client.get("/api/v1/fraud-alerts/grouped-by-type")
        assert response.status_code == 200
        data = response.json()
        for type_key, type_data in data["types"].items():
            items = type_data.get("items", [])
            for alert in items:
                assert "project_name" in alert, f"Alerta em '{type_key}' deve ter 'project_name'"
                assert alert["project_name"] is not None


# ============================================================
# Dashboard - Moeda EUR (NOVO)
# ============================================================
class TestDashboardEUR:

    @pytest.mark.asyncio
    async def test_dashboard_has_portfolio_value_eur(self, client, auth_token):
        """Dashboard deve retornar portfolio_value_eur."""
        response = await client.get(
            "/api/v1/dashboard/metrics",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "portfolio_value_eur" in data, "Deve ter 'portfolio_value_eur'"
        assert data["portfolio_value_eur"] > 0, "Valor do portfólio deve ser positivo"

    @pytest.mark.asyncio
    async def test_dashboard_no_usd_fields(self, client, auth_token):
        """Dashboard não deve ter campos _usd."""
        response = await client.get(
            "/api/v1/dashboard/metrics",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        for key in data.keys():
            assert "usd" not in key.lower(), f"Campo '{key}' não deveria conter 'usd'"
