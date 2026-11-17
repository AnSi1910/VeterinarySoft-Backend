"""Request and response validation with Pydantic v2."""
from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)


class UserRead(ReadModel):
    id: int
    email: EmailStr
    full_name: str
    role: Literal["owner", "admin"]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    species: str = Field(min_length=2, max_length=60)
    breed: str | None = Field(default=None, max_length=80)
    birth_date: date | None = None

    @field_validator("birth_date")
    @classmethod
    def not_future_birth(cls, value: date | None):
        if value is not None and value > datetime.now(timezone.utc).date():
            raise ValueError("Дата народження не може бути в майбутньому")
        return value


class PetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    species: str | None = Field(default=None, min_length=2, max_length=60)
    breed: str | None = Field(default=None, max_length=80)
    birth_date: date | None = None


class PetRead(ReadModel):
    id: int
    owner_id: int
    name: str
    species: str
    breed: str | None
    birth_date: date | None


class VeterinarianCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    specialization: str = Field(min_length=2, max_length=120)


class VeterinarianRead(ReadModel):
    id: int
    full_name: str
    specialization: str
    is_active: bool


class AppointmentCreate(BaseModel):
    pet_id: int = Field(gt=0)
    veterinarian_id: int = Field(gt=0)
    starts_at: datetime
    reason: str | None = Field(default=None, max_length=500)

    @field_validator("starts_at")
    @classmethod
    def valid_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Час потрібно передати з часовим поясом, наприклад +02:00")
        utc_value = value.astimezone(timezone.utc)
        if utc_value <= datetime.now(timezone.utc):
            raise ValueError("Час запису має бути в майбутньому")
        # SQLite stores UTC without timezone; all API datetimes are documented as UTC.
        return utc_value.replace(tzinfo=None)


class AppointmentStatusUpdate(BaseModel):
    status: Literal["confirmed", "completed", "cancelled"]


class AppointmentRead(ReadModel):
    id: int
    pet_id: int
    veterinarian_id: int
    starts_at: datetime
    reason: str | None
    status: Literal["pending", "confirmed", "completed", "cancelled"]


class MedicalRecordCreate(BaseModel):
    pet_id: int = Field(gt=0)
    veterinarian_id: int | None = Field(default=None, gt=0)
    visit_date: date
    diagnosis: str = Field(min_length=2, max_length=300)
    treatment: str | None = None
    notes: str | None = None


class MedicalRecordRead(ReadModel):
    id: int
    pet_id: int
    veterinarian_id: int | None
    visit_date: date
    diagnosis: str
    treatment: str | None
    notes: str | None


class ReminderCreate(BaseModel):
    pet_id: int = Field(gt=0)
    title: str = Field(min_length=2, max_length=160)
    remind_at: datetime

    @field_validator("remind_at")
    @classmethod
    def valid_reminder_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Потрібно вказати часовий пояс")
        return value.astimezone(timezone.utc).replace(tzinfo=None)


class ReminderRead(ReadModel):
    id: int
    pet_id: int
    title: str
    remind_at: datetime
    status: str
