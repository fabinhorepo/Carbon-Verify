"""Configuração do banco de dados SQLAlchemy async."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos."""
    pass


async def get_db() -> AsyncSession:
    """Dependency para injeção de sessão do banco."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Inicializa o banco de dados criando todas as tabelas."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
