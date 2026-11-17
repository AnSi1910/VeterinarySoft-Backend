"""FastAPI application entrypoint."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import appointments, auth, medical_records, pets, reminders, users, veterinarians


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # For a prototype. Production should use Alembic migrations.
    yield


app = FastAPI(
    title="VeterinarySoft API",
    version="0.1.0",
    description="Навчальний Backend: авторизація, тварини, ветеринари, медкартки, записи та нагадування. Час у відповідях API — UTC.",
    lifespan=lifespan,
)

allowed_origins = os.getenv("VET_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["GET", "POST", "PATCH", "DELETE"],
                   allow_headers=["Authorization", "Content-Type"])

for router in (auth.router, users.router, pets.router, veterinarians.router,
               appointments.router, medical_records.router, reminders.router):
    app.include_router(router)


@app.get("/", tags=["Стан сервера"])
def root():
    return {"project": "VeterinarySoft", "status": "ok", "documentation": "/docs"}


@app.get("/health", tags=["Стан сервера"])
def health():
    return {"status": "healthy"}
