from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Veterinarian
from ..schemas import VeterinarianCreate, VeterinarianRead
from ..security import admin_only

router = APIRouter(prefix="/api/veterinarians", tags=["Лікарі"])


@router.get("", response_model=list[VeterinarianRead])
def list_vets(db: Session = Depends(get_db)):
    return db.scalars(select(Veterinarian).where(Veterinarian.is_active.is_(True)).order_by(Veterinarian.id)).all()


@router.post("", response_model=VeterinarianRead, status_code=201)
def add_vet(data: VeterinarianCreate, _admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    vet = Veterinarian(**data.model_dump())
    db.add(vet)
    db.commit()
    db.refresh(vet)
    return vet


@router.patch("/{vet_id}/deactivate", response_model=VeterinarianRead)
def deactivate_vet(vet_id: int, _admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    vet = db.get(Veterinarian, vet_id)
    if vet is None:
        raise HTTPException(404, "Лікаря не знайдено")
    vet.is_active = False
    db.commit()
    db.refresh(vet)
    return vet
