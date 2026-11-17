from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Pet, Reminder, User
from ..schemas import ReminderCreate, ReminderRead
from ..security import current_user
from ..services import pet_for_user

router = APIRouter(prefix="/api/reminders", tags=["Нагадування"])


@router.post("", response_model=ReminderRead, status_code=201)
def add_reminder(data: ReminderCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    pet_for_user(db, data.pet_id, user)
    reminder = Reminder(**data.model_dump())
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("", response_model=list[ReminderRead])
def list_reminders(user: User = Depends(current_user), db: Session = Depends(get_db)):
    stmt = select(Reminder).join(Pet).order_by(Reminder.remind_at)
    if user.role != "admin":
        stmt = stmt.where(Pet.owner_id == user.id)
    return db.scalars(stmt).all()


@router.delete("/{reminder_id}", status_code=204)
def remove_reminder(reminder_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    reminder = db.get(Reminder, reminder_id)
    if reminder is None:
        raise HTTPException(404, "Нагадування не знайдено")
    pet_for_user(db, reminder.pet_id, user)
    db.delete(reminder)
    db.commit()
