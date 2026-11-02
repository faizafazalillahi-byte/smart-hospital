from datetime import datetime, date, time
from sqlalchemy import String, Integer, Float, Boolean, Date, Time, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))  # patient / doctor / reception / admin
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class Resource(Base):
    __tablename__ = "resources"  # rooms aur beds
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))          # e.g. "OPD Room 3", "Bed 12"
    type: Mapped[str] = mapped_column(String(20))           # room / bed
    status: Mapped[str] = mapped_column(String(20), default="available")  # available / occupied / maintenance


class Doctor(Base):
    __tablename__ = "doctors"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    room_id: Mapped[int | None] = mapped_column(ForeignKey("resources.id"), nullable=True)
    avg_consult_minutes: Mapped[int] = mapped_column(Integer, default=10)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)


class DoctorSchedule(Base):
    __tablename__ = "doctor_schedules"
    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    day_of_week: Mapped[int] = mapped_column(Integer)       # 0=Monday ... 6=Sunday
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    max_patients: Mapped[int] = mapped_column(Integer, default=30)


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)  # walk-in ka account nahi hota
    name: Mapped[str] = mapped_column(String(100))
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(10))
    phone: Mapped[str] = mapped_column(String(20))


class Appointment(Base):
    __tablename__ = "appointments"   # appointment + token + queue entry, sab yahin
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    appointment_date: Mapped[date] = mapped_column(Date)
    token_no: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(20), default="online")   # online / walkin
    status: Mapped[str] = mapped_column(String(20), default="waiting")  # waiting / in_consultation / completed / cancelled / no_show
    priority: Mapped[int] = mapped_column(Integer, default=3)           # 1=Critical, 2=High, 3=Medium, 4=Low
    est_wait_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    called_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class TriageRecord(Base):
    __tablename__ = "triage_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"))
    heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bp_systolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bp_diastolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    spo2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pain_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-10
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    predicted_priority: Mapped[int | None] = mapped_column(Integer, nullable=True)  # AI output (Stage 9)
