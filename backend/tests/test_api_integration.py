"""
Testes de integração para a API Carbon Verify.
Testa endpoints completos com banco de dados real e autenticação.
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
# Projetos (com paginação)
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
    async def test_list_projects_200_total(self, client):
        response = await client.get("/api/v1/projects?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 200, f"Deveria ter 200 projetos, tem {data['total']}"

    @pytest.mark.asyncio
    async def test_pagination_20_per_page(self, client):
        response = await client.get("/api/v1/projects?page=1&page_size=20")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 20
        assert data["page_size"] == 20
        assert data["total_pages"] == 10

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
        assert data["total"] == 100, f"Deveria ter 100 Verra, tem {data['total']}"
        for item in data["items"]:
            assert item["registry"] == "Verra"

    @pytest.mark.asyncio
    async def test_filter_by_registry_gold_standard(self, client):
        response = await client.get("/api/v1/projects?registry=Gold Standard")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100, f"Deveria ter 100 GS, tem {data['total']}"
        for item in data["items"]:
            assert item["registry"] == "Gold Standard"

    @pytest.mark.asyncio
    async def test_project_detail(self, client):
        response = await client.get("/api/v1/projects/1")
        assert response.status_code == 200
        data = response.json()
        # API pode retornar flat ou nested - verificar campos essenciais
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
        # Rating pode estar nested ou flat
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
# Fraud Alerts (com paginação)
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
    async def test_portfolio_recommendations_grouped(self, client, auth_token):
        response = await client.get(
            "/api/v1/portfolios/1?page=1&page_size=5",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        metrics = data["metrics"]
        assert "recommendations_grouped" in metrics
        grouped = metrics["recommendations_grouped"]
        assert isinstance(grouped, dict)
        # Deve ter pelo menos sell e hold
        assert "sell" in grouped, "Deveria ter recomendações de venda"
        assert "hold" in grouped, "Deveria ter recomendações de manter"

    @pytest.mark.asyncio
    async def test_portfolio_has_rebalance_tab(self, client, auth_token):
        response = await client.get(
            "/api/v1/portfolios/1?page=1&page_size=5",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        grouped = data["metrics"]["recommendations_grouped"]
        assert "rebalance" in grouped, "Deveria ter recomendações de rebalanceamento"
        assert len(grouped["rebalance"]) > 0


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
        assert data["total_projects"] == 200
        assert "avg_quality_score" in data
        assert "grade_distribution" in data
        assert "risk_summary" in data

    @pytest.mark.asyncio
    async def test_dashboard_score_distribution(self, client, auth_token):
        """Verifica distribuição 60/30/10 no dashboard."""
        response = await client.get(
            "/api/v1/dashboard/metrics",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        risk = data["risk_summary"]
        total = risk.get("high_risk", 0) + risk.get("medium_risk", 0) + risk.get("low_risk", 0)
        assert total == 200, f"Total deveria ser 200, é {total}"
        # Verificar proporções aproximadas
        high_pct = risk.get("high_risk", 0) / total * 100
        medium_pct = risk.get("medium_risk", 0) / total * 100
        low_pct = risk.get("low_risk", 0) / total * 100
        assert high_pct >= 5, f"High risk {high_pct:.0f}% deveria ser >= 5%"
        assert medium_pct >= 20, f"Medium risk {medium_pct:.0f}% deveria ser >= 20%"
        assert low_pct >= 45, f"Low risk {low_pct:.0f}% deveria ser >= 45%"

    @pytest.mark.asyncio
    async def test_dashboard_unauthorized(self, client):
        response = await client.get("/api/v1/dashboard/metrics")
        assert response.status_code in (401, 403), f"Esperado 401 ou 403, recebeu {response.status_code}"


# ============================================================
# Risk Matrix
# ============================================================
class TestRiskMatrix:

    @pytest.mark.asyncio
    async def test_risk_matrix(self, client, auth_token):
        response = await client.get(
            "/api/v1/dashboard/risk-matrix",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            item = data[0]
            assert "project_id" in item
            assert "name" in item
            # O campo pode ser 'score' ou 'overall_score'
            assert "score" in item or "overall_score" in item or "grade" in item
