from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserRead, UserUpdate
from ..security import admin_only, current_user

router = APIRouter(prefix="/api/users", tags=["Користувачі"])


@router.get("/me", response_model=UserRead)
def profile(user: User = Depends(current_user)):
    return user


@router.patch("/me", response_model=UserRead)
def edit_profile(data: UserUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.full_name = data.full_name.strip()
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UserRead])
def all_users(_admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.id)).all()


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, _admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "Користувача не знайдено")
    return user
