"""Endpoints de autenticação e registro."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.auth import verify_password, get_password_hash, create_access_token, create_api_key
from app.models.models import User, Organization, UserRole
from app.models.schemas import LoginRequest, TokenResponse, RegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Registra um novo usuário e organização."""
    # Verificar se email já existe
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Criar ou buscar organização
    slug = data.organization_name.lower().replace(" ", "-")[:100]
    org_result = await db.execute(select(Organization).where(Organization.slug == slug))
    org = org_result.scalar_one_or_none()
    
    if not org:
        org = Organization(name=data.organization_name, slug=slug)
        db.add(org)
        await db.flush()
        org.api_key = create_api_key(org.id)
    
    # Criar usuário
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        role=UserRole.ADMIN,
        organization_id=org.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Gerar token
    token = create_access_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Autentica um usuário e retorna token JWT."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")
    
    token = create_access_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        __import__("app.core.auth", fromlist=["get_current_user"]).get_current_user
    ),
):
    """Retorna dados do usuário autenticado."""
    return UserResponse.model_validate(current_user)
