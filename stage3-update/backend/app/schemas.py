from datetime import date, time, datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field


class PatientRegister(BaseModel):
    """Patient khud register karta hai (role hamesha 'patient' hota hai)."""
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=64)
    age: int = Field(ge=0, le=120)
    gender: Literal["male", "female", "other"]
    phone: str = Field(min_length=7, max_length=20)


class StaffCreate(BaseModel):
    """Sirf admin staff account banata hai."""
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=64)
    role: Literal["doctor", "reception", "admin"]


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


# ---------------- Stage 3: Departments, Doctors, Schedules, Appointments ----------------
class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class DepartmentOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ScheduleCreate(BaseModel):
    day_of_week: int = Field(ge=0, le=6, description="0=Monday ... 6=Sunday")
    start_time: time
    end_time: time
    max_patients: int = Field(default=30, ge=1, le=200)


class ScheduleOut(BaseModel):
    id: int
    day_of_week: int
    start_time: time
    end_time: time
    max_patients: int

    model_config = {"from_attributes": True}


class DoctorCreate(BaseModel):
    user_id: int
    department_id: int
    room_id: Optional[int] = None
    avg_consult_minutes: int = Field(default=10, ge=1, le=120)


class AvailabilityUpdate(BaseModel):
    is_available: bool


class DoctorOut(BaseModel):
    id: int
    user_id: int
    name: str
    department_id: int
    department_name: str
    room_id: Optional[int]
    avg_consult_minutes: int
    is_available: bool
    schedules: list[ScheduleOut]


class SlotInfo(BaseModel):
    doctor_id: int
    date: date
    schedules: list[ScheduleOut]
    total_capacity: int
    booked: int
    remaining: int
    can_book: bool
    message: str


class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_date: date


class WalkInCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0, le=120)
    gender: Literal["male", "female", "other"]
    phone: str = Field(min_length=7, max_length=20)
    doctor_id: int


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    patient_name: str
    doctor_id: int
    doctor_name: str
    appointment_date: date
    token_no: int
    source: str
    status: str
    priority: int
    est_wait_minutes: Optional[int]
    created_at: datetime
