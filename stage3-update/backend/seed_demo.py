"""Demo data: departments, rooms, 3 doctors (schedule ke saath). Sirf testing ke liye, dobara chalane se duplicate nahi banta."""
from datetime import time
from sqlalchemy import select

from app.database import SessionLocal
from app.models import User, Department, Resource, Doctor, DoctorSchedule
from app.security import hash_password

DEPARTMENTS = ["General Medicine", "Cardiology", "Pediatrics", "Orthopedics"]

DOCTORS = [
    # (naam, email, department, room)
    ("Dr. Ahmed Khan", "ahmed@hospital.com", "General Medicine", "OPD Room 1"),
    ("Dr. Sara Malik", "sara@hospital.com", "Cardiology", "OPD Room 2"),
    ("Dr. Bilal Raza", "bilal@hospital.com", "Pediatrics", "OPD Room 3"),
]
DOCTOR_PASSWORD = "doctor123"

db = SessionLocal()

for name in DEPARTMENTS:
    if not db.scalar(select(Department).where(Department.name == name)):
        db.add(Department(name=name))
db.commit()

for _, _, _, room in DOCTORS:
    if not db.scalar(select(Resource).where(Resource.name == room)):
        db.add(Resource(name=room, type="room", status="available"))
for i in range(1, 6):
    bed = f"Bed {i}"
    if not db.scalar(select(Resource).where(Resource.name == bed)):
        db.add(Resource(name=bed, type="bed", status="available"))
db.commit()

for name, email, dept_name, room_name in DOCTORS:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(name=name, email=email, password_hash=hash_password(DOCTOR_PASSWORD), role="doctor")
        db.add(user)
        db.commit()
        db.refresh(user)

    if db.scalar(select(Doctor).where(Doctor.user_id == user.id)):
        continue

    dept = db.scalar(select(Department).where(Department.name == dept_name))
    room = db.scalar(select(Resource).where(Resource.name == room_name))
    doctor = Doctor(user_id=user.id, department_id=dept.id, room_id=room.id, avg_consult_minutes=10)
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    # Monday se Saturday, subah 9 se raat 9 tak (demo ke liye lambi timing)
    for day in range(0, 6):
        db.add(DoctorSchedule(doctor_id=doctor.id, day_of_week=day,
                              start_time=time(9, 0), end_time=time(21, 0), max_patients=30))
    db.commit()

print("Demo data ban gaya!")
print("Doctor login: ahmed@hospital.com / sara@hospital.com / bilal@hospital.com")
print("Password:", DOCTOR_PASSWORD)
