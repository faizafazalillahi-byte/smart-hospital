from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_roles
from ..models import Doctor, DoctorSchedule, Department, Resource, User
from ..schemas import (DoctorCreate, DoctorOut, ScheduleCreate, ScheduleOut,
                       AvailabilityUpdate, SlotInfo)
from ..services.booking import check_bookable

router = APIRouter(prefix="/doctors", tags=["Doctors"])


def doctor_to_out(db: Session, doctor: Doctor) -> DoctorOut:
    user = db.get(User, doctor.user_id)
    dept = db.get(Department, doctor.department_id)
    schedules = db.scalars(
        select(DoctorSchedule).where(DoctorSchedule.doctor_id == doctor.id)
        .order_by(DoctorSchedule.day_of_week, DoctorSchedule.start_time)
    ).all()
    return DoctorOut(
        id=doctor.id, user_id=doctor.user_id, name=user.name,
        department_id=doctor.department_id, department_name=dept.name,
        room_id=doctor.room_id, avg_consult_minutes=doctor.avg_consult_minutes,
        is_available=doctor.is_available,
        schedules=[ScheduleOut.model_validate(s) for s in schedules],
    )


def get_doctor_or_404(db: Session, doctor_id: int) -> Doctor:
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor nahi mila.")
    return doctor


def ensure_admin_or_self(doctor: Doctor, user: User):
    """Sirf admin ya khud wohi doctor apni schedule badal sakta hai."""
    if user.role != "admin" and doctor.user_id != user.id:
        raise HTTPException(status_code=403, detail="Aap sirf apni schedule badal sakte hain.")


@router.post("", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(data: DoctorCreate, db: Session = Depends(get_db),
                  _admin: User = Depends(require_roles("admin"))):
    """Admin kisi 'doctor' role wale user ka doctor profile banata hai."""
    user = db.get(User, data.user_id)
    if user is None or user.role != "doctor":
        raise HTTPException(status_code=400, detail="Ye user maujood nahi ya uska role 'doctor' nahi hai.")
    if db.scalar(select(Doctor).where(Doctor.user_id == data.user_id)):
        raise HTTPException(status_code=400, detail="Is user ka doctor profile pehle se hai.")
    if db.get(Department, data.department_id) is None:
        raise HTTPException(status_code=400, detail="Department nahi mila.")
    if data.room_id is not None:
        room = db.get(Resource, data.room_id)
        if room is None or room.type != "room":
            raise HTTPException(status_code=400, detail="Room nahi mila.")

    doctor = Doctor(user_id=data.user_id, department_id=data.department_id,
                    room_id=data.room_id, avg_consult_minutes=data.avg_consult_minutes)
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor_to_out(db, doctor)


@router.get("", response_model=list[DoctorOut])
def list_doctors(department_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    """Doctors ki list, timing ke saath (public). ?department_id= se filter."""
    query = select(Doctor).order_by(Doctor.id)
    if department_id is not None:
        query = query.where(Doctor.department_id == department_id)
    return [doctor_to_out(db, d) for d in db.scalars(query).all()]


@router.get("/me/profile", response_model=DoctorOut)
def my_profile(db: Session = Depends(get_db), user: User = Depends(require_roles("doctor"))):
    """Login doctor ka apna profile."""
    doctor = db.scalar(select(Doctor).where(Doctor.user_id == user.id))
    if doctor is None:
        raise HTTPException(status_code=404, detail="Aap ka doctor profile abhi nahi bana. Admin se kahein.")
    return doctor_to_out(db, doctor)


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    return doctor_to_out(db, get_doctor_or_404(db, doctor_id))


@router.get("/{doctor_id}/slots", response_model=SlotInfo)
def doctor_slots(doctor_id: int, day: date = Query(alias="date"), db: Session = Depends(get_db)):
    """Kisi date par doctor ki availability: timing, total tokens, booked, remaining."""
    doctor = get_doctor_or_404(db, doctor_id)
    ok, message, schedules, capacity, booked = check_bookable(db, doctor, day)
    return SlotInfo(
        doctor_id=doctor.id, date=day,
        schedules=[ScheduleOut.model_validate(s) for s in schedules],
        total_capacity=capacity, booked=booked,
        remaining=max(capacity - booked, 0), can_book=ok, message=message,
    )


@router.post("/{doctor_id}/schedules", response_model=ScheduleOut, status_code=status.HTTP_201_CREATED)
def add_schedule(doctor_id: int, data: ScheduleCreate, db: Session = Depends(get_db),
                 user: User = Depends(require_roles("admin", "doctor"))):
    doctor = get_doctor_or_404(db, doctor_id)
    ensure_admin_or_self(doctor, user)
    if data.end_time <= data.start_time:
        raise HTTPException(status_code=400, detail="End time, start time se baad ka hona chahiye.")
    schedule = DoctorSchedule(doctor_id=doctor_id, **data.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db),
                    user: User = Depends(require_roles("admin", "doctor"))):
    schedule = db.get(DoctorSchedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule nahi mili.")
    ensure_admin_or_self(get_doctor_or_404(db, schedule.doctor_id), user)
    db.delete(schedule)
    db.commit()


@router.patch("/{doctor_id}/availability", response_model=DoctorOut)
def set_availability(doctor_id: int, data: AvailabilityUpdate, db: Session = Depends(get_db),
                     user: User = Depends(require_roles("admin", "doctor"))):
    """Doctor available / chutti par (on-off)."""
    doctor = get_doctor_or_404(db, doctor_id)
    ensure_admin_or_self(doctor, user)
    doctor.is_available = data.is_available
    db.commit()
    return doctor_to_out(db, doctor)
