from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import MedicalRecord, User, Veterinarian
from ..schemas import MedicalRecordCreate, MedicalRecordRead
from ..security import admin_only, current_user
from ..services import pet_for_user

router = APIRouter(prefix="/api/medical-records", tags=["Медкартки"])


@router.post("", response_model=MedicalRecordRead, status_code=201)
def add_record(data: MedicalRecordCreate, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    pet_for_user(db, data.pet_id, admin)
    if data.veterinarian_id is not None and db.get(Veterinarian, data.veterinarian_id) is None:
        raise HTTPException(404, "Лікаря не знайдено")
    record = MedicalRecord(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/pet/{pet_id}", response_model=list[MedicalRecordRead])
def records_for_pet(pet_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    pet_for_user(db, pet_id, user)
    return db.scalars(select(MedicalRecord).where(MedicalRecord.pet_id == pet_id)
                      .order_by(MedicalRecord.visit_date.desc())).all()
