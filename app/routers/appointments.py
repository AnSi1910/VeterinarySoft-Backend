from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Appointment, Pet, User, Veterinarian
from ..schemas import AppointmentCreate, AppointmentRead, AppointmentStatusUpdate
from ..security import current_user
from ..services import pet_for_user

router = APIRouter(prefix="/api/appointments", tags=["Записи на прийом"])


def visible_appointment(db: Session, appointment_id: int, user: User) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None or (user.role != "admin" and appointment.pet.owner_id != user.id):
        raise HTTPException(status_code=404, detail="Запис не знайдено")
    return appointment


@router.post("", response_model=AppointmentRead, status_code=201)
def create_appointment(data: AppointmentCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    pet_for_user(db, data.pet_id, user)
    vet = db.get(Veterinarian, data.veterinarian_id)
    if vet is None or not vet.is_active:
        raise HTTPException(status_code=404, detail="Активного лікаря не знайдено")
    appointment = Appointment(**data.model_dump())
    db.add(appointment)
    try:
        db.commit()  # DB's unique partial index prevents double-booking, even on concurrent requests.
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Цей час у лікаря вже зайнятий") from None
    db.refresh(appointment)
    return appointment


@router.get("", response_model=list[AppointmentRead])
def list_appointments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    stmt = select(Appointment).join(Pet, Appointment.pet_id == Pet.id).order_by(Appointment.starts_at)
    if user.role != "admin":
        stmt = stmt.where(Pet.owner_id == user.id)
    return db.scalars(stmt).all()


@router.get("/{appointment_id}", response_model=AppointmentRead)
def get_appointment(appointment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return visible_appointment(db, appointment_id, user)


@router.patch("/{appointment_id}/status", response_model=AppointmentRead)
def update_status(appointment_id: int, data: AppointmentStatusUpdate,
                  user: User = Depends(current_user), db: Session = Depends(get_db)):
    appointment = visible_appointment(db, appointment_id, user)
    if appointment.status in {"completed", "cancelled"}:
        raise HTTPException(status_code=409, detail="Завершений або скасований запис не можна змінити")
    if user.role != "admin" and data.status != "cancelled":
        raise HTTPException(status_code=403, detail="Підтвердити або завершити запис може лише адміністратор")
    if user.role == "admin" and data.status == "completed" and appointment.status != "confirmed":
        raise HTTPException(status_code=409, detail="Спершу підтвердіть запис")
    appointment.status = data.status
    db.commit()
    db.refresh(appointment)
    return appointment
