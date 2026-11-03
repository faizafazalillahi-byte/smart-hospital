"""Pehla admin account banane ke liye (sirf ek baar chalayein)."""
from getpass import getpass
from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.security import hash_password

name = input("Admin ka naam: ").strip()
email = input("Admin ki email: ").strip().lower()
password = getpass("Password (kam az kam 6 characters): ")

if len(name) < 2 or len(password) < 6 or len(password) > 64:
    raise SystemExit("Naam kam az kam 2 aur password 6 se 64 characters ka hona chahiye.")

db = SessionLocal()
if db.scalar(select(User).where(User.email == email)):
    raise SystemExit("Ye email pehle se maujood hai.")

db.add(User(name=name, email=email, password_hash=hash_password(password), role="admin"))
db.commit()
print("Admin account ban gaya!")
