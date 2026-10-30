"""Authentication endpoints: register, login, me."""
from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from sqlalchemy.orm import Session

from ..core.security import create_access_token, hash_password, verify_password
from ..core.deps import _db, UserDep, AdminDep
from ..database import get_db
from ..models import User, UserRole
from ..schemas.auth import (
    LoginRequest,
    RegisterRequest,
    Token,
    UserCreate,
    UserOut,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: _db) -> Token:
    if db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.email)
    ).first():
        raise HTTPException(status_code=400, detail="Username or email already registered")
    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=UserRole.ANALYST,  # self-registration never grants admin
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=user.username, role=user.role, user_id=user.id)
    return Token(access_token=token, role=user.role, username=user.username, user_id=user.id)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: _db) -> Token:
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    token = create_access_token(subject=user.username, role=user.role, user_id=user.id)
    return Token(access_token=token, role=user.role, username=user.username, user_id=user.id)


@router.get("/me", response_model=UserOut)
def me(user: UserDep) -> User:
    return user


# ---- Admin user management -------------------------------------------------

@router.get("/users", response_model=list[UserOut])
def list_users(_: AdminDep, db: _db) -> list[User]:
    return db.query(User).all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, _: AdminDep, db: _db) -> User:
    if db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.email)
    ).first():
        raise HTTPException(status_code=400, detail="Username or email already registered")
    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, _: AdminDep, db: _db) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    data = payload.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        data["hashed_password"] = hash_password(data.pop("password"))
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user