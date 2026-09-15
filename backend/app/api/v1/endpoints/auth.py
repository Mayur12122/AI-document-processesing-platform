from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user_org import User, Organization, OrganizationMember, UserRole
from app.api.deps import get_current_user, get_current_organization

router = APIRouter()

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: Optional[str] = "Acme India Corp"

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
        
    hashed = get_password_hash(data.password)
    user = User(
        email=data.email,
        hashed_password=hashed,
        full_name=data.full_name,
        role=UserRole.ADMIN
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create Organization for user
    org_slug = data.organization_name.lower().replace(" ", "-") + f"-{user.id.hex[:6]}"
    org = Organization(name=data.organization_name, slug=org_slug)
    db.add(org)
    await db.commit()
    await db.refresh(org)

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=UserRole.ADMIN
    )
    db.add(member)
    await db.commit()

    token = create_access_token(subject=str(user.id), organization_id=str(org.id), role=user.role.value)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value
        )
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value
        )
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value
    )
