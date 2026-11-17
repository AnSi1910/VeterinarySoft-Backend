"""Relational database schema for VeterinarySoft."""
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(12), default="owner", nullable=False)  # owner | admin
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    pets: Mapped[list["Pet"]] = relationship(back_populates="owner")


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    species: Mapped[str] = mapped_column(String(60), nullable=False)
    breed: Mapped[str | None] = mapped_column(String(80), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    owner: Mapped[User] = relationship(back_populates="pets")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="pet")
    records: Mapped[list["MedicalRecord"]] = relationship(back_populates="pet")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="pet")


class Veterinarian(Base):
    __tablename__ = "veterinarians"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    specialization: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="veterinarian")
    records: Mapped[list["MedicalRecord"]] = relationship(back_populates="veterinarian")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id", ondelete="RESTRICT"), index=True)
    veterinarian_id: Mapped[int] = mapped_column(ForeignKey("veterinarians.id", ondelete="RESTRICT"), index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)  # pending, confirmed, completed, cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    pet: Mapped[Pet] = relationship(back_populates="appointments")
    veterinarian: Mapped[Veterinarian] = relationship(back_populates="appointments")

    __table_args__ = (
        Index(
            "uq_active_vet_datetime", "veterinarian_id", "starts_at", unique=True,
            sqlite_where=text("status IN ('pending', 'confirmed')"),
            postgresql_where=text("status IN ('pending', 'confirmed')"),
        ),
    )


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id", ondelete="RESTRICT"), index=True)
    veterinarian_id: Mapped[int | None] = mapped_column(ForeignKey("veterinarians.id", ondelete="SET NULL"))
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)
    diagnosis: Mapped[str] = mapped_column(String(300), nullable=False)
    treatment: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    pet: Mapped[Pet] = relationship(back_populates="records")
    veterinarian: Mapped[Veterinarian | None] = relationship(back_populates="records")


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)

    pet: Mapped[Pet] = relationship(back_populates="reminders")
