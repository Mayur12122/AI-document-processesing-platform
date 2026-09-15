from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import verify_token
from app.models.user_org import User, Organization, OrganizationMember

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if not payload or "sub" not in payload:
        raise credentials_exception
        
    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise credentials_exception
    return user

async def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Organization:
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember)
        .where(OrganizationMember.user_id == current_user.id)
    )
    org = result.scalars().first()
    
    if not org:
        # Auto-create default demo organization if user belongs to none
        org = Organization(name="Default Organization", slug=f"org-{current_user.id.hex[:8]}")
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
        member = OrganizationMember(organization_id=org.id, user_id=current_user.id, role=current_user.role)
        db.add(member)
        await db.commit()

    return org
