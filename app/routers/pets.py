from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Appointment, MedicalRecord, Pet, Reminder, User
from ..schemas import PetCreate, PetRead, PetUpdate
from ..security import current_user
from ..services import pet_for_user

router = APIRouter(prefix="/api/pets", tags=["Тварини"])


@router.post("", response_model=PetRead, status_code=201)
def create_pet(data: PetCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    pet = Pet(owner_id=user.id, **data.model_dump())
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


@router.get("", response_model=list[PetRead])
def list_pets(user: User = Depends(current_user), db: Session = Depends(get_db)):
    stmt = select(Pet).order_by(Pet.id)
    if user.role != "admin":
        stmt = stmt.where(Pet.owner_id == user.id)
    return db.scalars(stmt).all()


@router.get("/{pet_id}", response_model=PetRead)
def get_pet(pet_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return pet_for_user(db, pet_id, user)


@router.patch("/{pet_id}", response_model=PetRead)
def edit_pet(pet_id: int, data: PetUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    pet = pet_for_user(db, pet_id, user)
    for key, value in data.model_dump(exclude_unset=True).items():
        if key in {"name", "species"} and value is None:
            raise HTTPException(status_code=422, detail=f"Поле {key} не може бути порожнім")
        setattr(pet, key, value)
    db.commit()
    db.refresh(pet)
    return pet


@router.delete("/{pet_id}", status_code=204)
def delete_pet(pet_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    pet = pet_for_user(db, pet_id, user)
    # Preserve medical history and appointment references; don't silently cascade-delete.
    if any(db.scalar(select(model.id).where(model.pet_id == pet_id).limit(1)) is not None
           for model in (Appointment, MedicalRecord, Reminder)):
        raise HTTPException(409, "Неможливо видалити тварину, поки є пов'язані записи")
    db.delete(pet)
    db.commit()
