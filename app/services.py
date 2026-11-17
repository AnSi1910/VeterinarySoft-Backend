"""Shared access-control checks (business rules)."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .models import Pet, User


def pet_for_user(db: Session, pet_id: int, user: User) -> Pet:
    pet = db.get(Pet, pet_id)
    # A 404 rather than 403 avoids exposing other owners' pet IDs.
    if pet is None or (user.role != "admin" and pet.owner_id != user.id):
        raise HTTPException(status_code=404, detail="Тварину не знайдено")
    return pet
