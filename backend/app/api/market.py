"""
Endpoints de Mercado - Cotação de Crédito de Carbono em Tempo Real.
"""
from fastapi import APIRouter

from app.services.carbon_price import get_carbon_price, get_market_summary

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/carbon-price")
async def carbon_price():
    """
    Retorna cotação atual do crédito de carbono EU ETS em EUR.
    
    Atualizado a cada 5 minutos. Fonte: EU ETS (ICE Endex).
    Fallback para estimativa baseada em dados de mercado se API externa indisponível.
    """
    return await get_carbon_price()


@router.get("/summary")
async def market_summary():
    """
    Retorna resumo dos principais mercados de carbono.
    Inclui EU ETS, Verra (VCS) e Gold Standard.
    """
    return get_market_summary()
