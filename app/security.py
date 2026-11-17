"""JWT access tokens and Argon2id password hashing."""
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

_password_hasher = PasswordHasher()
# Random development secret. Set VET_SECRET_KEY in the environment for stable sessions.
SECRET_KEY = os.getenv("VET_SECRET_KEY") or secrets.token_urlsafe(48)
TOKEN_EXPIRY_MINUTES = 60
bearer = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def check_password(password: str, stored_hash: str) -> bool:
    try:
        return _password_hasher.verify(stored_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def create_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "iat": now, "exp": now + timedelta(minutes=TOKEN_EXPIRY_MINUTES)},
        SECRET_KEY, algorithm="HS256",
    )


def current_user(token: str = Depends(bearer), db: Session = Depends(get_db)) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недійсний або прострочений токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        claims = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        uid = int(claims["sub"])
        if uid <= 0:
            raise ValueError
    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        raise unauthorized from None
    user = db.get(User, uid)
    if user is None:
        raise unauthorized
    return user


def admin_only(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Потрібна роль адміністратора")
    return user
