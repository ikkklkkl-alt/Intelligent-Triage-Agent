from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Role, User
from app.schemas import RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
async def register(data: RegisterIn, db: AsyncSession = Depends(get_db)):
    exists = await db.scalar(select(User).where(User.username == data.username))
    if exists: raise HTTPException(400, "用户名已存在")
    user = User(username=data.username, password_hash=hash_password(data.password), full_name=data.full_name, phone=data.phone, role=Role.patient)
    db.add(user); await db.commit(); await db.refresh(user); return user

@router.post("/login", response_model=TokenOut)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.username == form.username))
    if not user or not verify_password(form.password, user.password_hash): raise HTTPException(401, "用户名或密码错误")
    return TokenOut(access_token=create_access_token(user.id, user.role.value))

@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
