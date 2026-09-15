import enum
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    REVIEWER = "REVIEWER"
    USER = "USER"

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")

class Organization(BaseModel):
    __tablename__ = "organizations"

    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)

    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="organization", cascade="all, delete-orphan")

class OrganizationMember(BaseModel):
    __tablename__ = "organization_members"

    organization_id = Column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="memberships")
