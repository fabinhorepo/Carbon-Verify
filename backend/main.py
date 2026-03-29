"""
Carbon Verify MVP - Aplicação Principal
Plataforma B2B SaaS de verificação e due diligence de créditos de carbono.
"""
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Adicionar o diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import init_db, async_session
from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.fraud import router as fraud_router
from app.api.portfolio import router as portfolio_router, dashboard_router


async def seed_database():
    """Popula o banco com dados de demonstração."""
    from sqlalchemy import select
    from app.models.models import (
        Organization, User, CarbonProject, CarbonCredit,
        Portfolio, PortfolioPosition
    )
    from app.core.auth import get_password_hash, create_api_key
    from app.services.rating_engine import calculate_rating
    from app.services.fraud_detection import run_fraud_detection
    from app.data.seed_data import SEED_PROJECTS, SEED_CREDITS
    from datetime import datetime, timezone

    async with async_session() as db:
        # Verificar se já tem dados
        result = await db.execute(select(Organization))
        if result.scalar_one_or_none():
            return
        
        # Criar organização demo
        org = Organization(
            name="Carbon Verify Demo",
            slug="carbon-verify-demo",
            plan="enterprise",
            rate_limit=1000,
        )
        db.add(org)
        await db.flush()
        org.api_key = create_api_key(org.id)
        
        # Criar usuário demo
        user = User(
            email="demo@carbonverify.com",
            hashed_password=get_password_hash("demo123"),
            full_name="Demo User",
            role="admin",
            organization_id=org.id,
        )
        db.add(user)
        
        # Criar projetos
        project_objects = []
        for proj_data in SEED_PROJECTS:
            project = CarbonProject(**proj_data)
            db.add(project)
            await db.flush()
            project_objects.append(project)
            
            # Calcular rating
            rating = calculate_rating(project)
            db.add(rating)
            
            # Executar fraud detection
            alerts = run_fraud_detection(project)
            for alert in alerts:
                db.add(alert)
        
        # Criar créditos
        credit_objects = []
        for credit_data in SEED_CREDITS:
            project = project_objects[credit_data["project_idx"]]
            credit = CarbonCredit(
                serial_number=credit_data["serial_number"],
                project_id=project.id,
                vintage_year=credit_data["vintage_year"],
                quantity=credit_data["quantity"],
                status=credit_data["status"],
                price_usd=credit_data["price_usd"],
                issuance_date=datetime.now(timezone.utc),
            )
            db.add(credit)
            await db.flush()
            credit_objects.append(credit)
        
        # Criar portfólio demo
        portfolio = Portfolio(
            name="Portfólio Principal ESG",
            organization_id=org.id,
            description="Portfólio diversificado de créditos de carbono para compensação corporativa",
        )
        db.add(portfolio)
        await db.flush()
        
        # Adicionar posições ao portfólio
        total_credits = 0
        total_value = 0.0
        for credit in credit_objects:
            qty = credit.quantity // 2  # Metade de cada crédito
            price = credit.price_usd or 10.0
            position = PortfolioPosition(
                portfolio_id=portfolio.id,
                credit_id=credit.id,
                quantity=qty,
                acquisition_price_usd=price,
                acquisition_date=datetime.now(timezone.utc),
            )
            db.add(position)
            total_credits += qty
            total_value += qty * price
        
        portfolio.total_credits = total_credits
        portfolio.total_value_usd = total_value
        
        # Calcular score médio do portfólio
        from app.models.models import ProjectRating
        ratings = await db.execute(select(ProjectRating))
        all_ratings = ratings.scalars().all()
        if all_ratings:
            portfolio.avg_quality_score = sum(r.overall_score for r in all_ratings) / len(all_ratings)
        
        await db.commit()
        print("✅ Banco de dados populado com dados de demonstração")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle do aplicativo."""
    await init_db()
    await seed_database()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas da API
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(fraud_router, prefix=settings.API_V1_PREFIX)
app.include_router(portfolio_router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)


# Health check
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# Servir frontend estático
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve o frontend React para qualquer rota não-API."""
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))
