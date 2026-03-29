# Carbon Verify MVP

**Plataforma B2B SaaS de Verificação e Due Diligence de Créditos de Carbono**

## Visão Geral

Carbon Verify é uma plataforma que oferece verificação automatizada e due diligence de créditos de carbono, incluindo:

- **Rating de Qualidade (AAA-D)**: Motor de regras/scorecard com 7 dimensões de avaliação
- **Fraud Detection**: Detecção de inconsistências e sinais de fraude em projetos
- **Dashboard de Portfólio**: Métricas agregadas, risco e recomendações de rebalanceamento
- **API REST**: Integração com marketplaces e softwares ESG via API documentada

## Stack Tecnológica

| Componente | Tecnologia |
|-----------|-----------|
| Backend | Python 3.11 + FastAPI |
| Banco de Dados | SQLite + SQLAlchemy Async |
| Frontend | React + TypeScript + TailwindCSS |
| Gráficos | Recharts |
| Autenticação | JWT (Bearer Token) |
| Deploy | Render (Free Tier) |

## Arquitetura

```
carbon-verify/
├── backend/
│   ├── app/
│   │   ├── api/          # Endpoints REST
│   │   ├── core/         # Config, Auth, Database
│   │   ├── data/         # Seed data
│   │   ├── models/       # SQLAlchemy models + Pydantic schemas
│   │   └── services/     # Rating Engine, Fraud Detection, Analytics
│   ├── static/           # Frontend build (servido pelo FastAPI)
│   └── main.py           # Aplicação principal
├── frontend/
│   └── src/
│       ├── components/   # Layout, Sidebar
│       ├── pages/        # Dashboard, Projects, FraudAlerts, Portfolio, ApiDocs
│       └── utils/        # API client, helpers
├── Dockerfile
├── render.yaml
└── README.md
```

## Módulos do MVP

### 1. Rating de Qualidade (AAA-D)
- 7 dimensões: Adicionalidade, Permanência, Leakage, MRV, Co-benefícios, Governança, Baseline
- Pesos configuráveis por dimensão
- Escala AAA (>90) a D (<20)
- Explicação textual e flags de risco

### 2. Fraud Detection
- 6 tipos de alerta: overcrediting, vintage_age, retirement_anomaly, missing_area, governance_gaps, insufficient_buffer
- 4 níveis de severidade: critical, high, medium, low
- Workflow de revisão: open → under_review → confirmed/dismissed

### 3. Dashboard de Portfólio
- KPIs: projetos, score médio, alertas, valor do portfólio
- Distribuição de ratings, tipos, países
- Matriz de risco (scatter plot)
- Recomendações de rebalanceamento

### 4. API REST
- Documentação Swagger UI em `/api/docs`
- Documentação ReDoc em `/api/redoc`
- OpenAPI spec em `/api/openapi.json`
- Autenticação JWT Bearer Token

## Credenciais de Demo

| Campo | Valor |
|-------|-------|
| Email | demo@carbonverify.com |
| Senha | demo123 |

## Deploy na Render

### Via Docker (Recomendado)
1. Faça push do código para um repositório GitHub
2. No Render Dashboard, crie um novo **Web Service**
3. Conecte o repositório GitHub
4. Selecione **Docker** como runtime
5. O Dockerfile já está configurado para a porta 10000
6. Adicione a variável de ambiente `SECRET_KEY` (gere uma chave aleatória)

### Via render.yaml (Blueprint)
1. Faça push do código para GitHub
2. No Render, vá em **Blueprints** e conecte o repositório
3. O `render.yaml` configura tudo automaticamente

## Desenvolvimento Local

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Frontend
cd frontend
pnpm install
pnpm dev
```

## Licença

Proprietário - Carbon Verify © 2026
