"""
Configuração global dos testes.
Garante que o banco de dados de teste é criado e populado antes dos testes.
"""
import pytest
import asyncio
import os
import sys

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Usar banco de dados de teste - DEVE ser definido ANTES de importar qualquer módulo da app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_carbon_verify.db"

# Forçar recriação do settings com a nova DATABASE_URL
from app.core import config as config_module
config_module.settings = config_module.Settings()


@pytest.fixture(scope="session")
def event_loop():
    """Cria um event loop para toda a sessão de testes."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db(event_loop):
    """Inicializa o banco de dados de teste e popula com seed data."""
    import glob
    # Limpar banco de teste anterior
    for f in glob.glob("./test_carbon_verify.db*"):
        os.remove(f)

    async def _setup():
        from app.core.database import init_db, engine
        from main import seed_database
        await init_db()
        await seed_database()

    event_loop.run_until_complete(_setup())
    yield
    # Cleanup
    for f in glob.glob("./test_carbon_verify.db*"):
        try:
            os.remove(f)
        except Exception:
            pass
