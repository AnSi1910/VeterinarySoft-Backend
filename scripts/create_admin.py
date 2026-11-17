"""Run: python -m scripts.create_admin --email admin@example.com --name 'Clinic Admin'"""
import argparse
from getpass import getpass
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal, init_db
from app.models import User
from app.security import hash_password


def main():
    parser = argparse.ArgumentParser(description="Створити адміністратора VeterinarySoft")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    password = getpass("Пароль адміністратора (мінімум 8 символів): ")
    if len(password) < 8:
        parser.error("Пароль має містити мінімум 8 символів")
    init_db()
    with SessionLocal() as db:
        email = args.email.lower().strip()
        if db.scalar(select(User).where(User.email == email)):
            parser.error("Такий email уже існує")
        db.add(User(email=email, full_name=args.name.strip(), password_hash=hash_password(password), role="admin"))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            parser.error("Не вдалося створити адміністратора")
    print("Адміністратора створено.")


if __name__ == "__main__":
    main()
