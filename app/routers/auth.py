from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import Token, UserRead, UserRegister
from ..security import check_password, create_token, hash_password

router = APIRouter(prefix="/api/auth", tags=["Авторизація"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    # Public registration only creates an 'owner'; admin is created via CLI.
    user = User(email=str(data.email).lower(), full_name=data.full_name.strip(),
                password_hash=hash_password(data.password), role="owner")
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email уже зареєстрований") from None
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.strip().lower()))
    if user is None or not check_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неправильний email або пароль")
    return Token(access_token=create_token(user.id))
