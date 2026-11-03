"""Token booking ka shared logic (online patient aur walk-in dono yahi use karte hain)."""
from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..models import Doctor, DoctorSchedule, Appointment, Patient, User

MAX_DAYS_AHEAD = 14


def get_day_schedules(db: Session, doctor_id: int, day: date):
    """Is doctor ki us din (weekday) ki schedules."""
    return db.scalars(
        select(DoctorSchedule)
        .where(DoctorSchedule.doctor_id == doctor_id,
               DoctorSchedule.day_of_week == day.weekday())
        .order_by(DoctorSchedule.start_time)
    ).all()


def count_booked(db: Session, doctor_id: int, day: date) -> int:
    """Cancel ke baghair kitne tokens ban chuke hain."""
    return db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == day,
            Appointment.status != "cancelled",
        )
    ) or 0


def check_bookable(db: Session, doctor: Doctor, day: date):
    """(can_book, message, schedules, capacity, booked) wapas karta hai."""
    schedules = get_day_schedules(db, doctor.id, day)
    capacity = sum(s.max_patients for s in schedules)
    booked = count_booked(db, doctor.id, day)

    today = date.today()
    if not doctor.is_available:
        return False, "Doctor abhi available nahi hain.", schedules, capacity, booked
    if day < today:
        return False, "Purani date par booking nahi ho sakti.", schedules, capacity, booked
    if day > today + timedelta(days=MAX_DAYS_AHEAD):
        return False, f"Sirf agle {MAX_DAYS_AHEAD} din tak booking hoti hai.", schedules, capacity, booked
    if not schedules:
        return False, "Doctor us din available nahi hain.", schedules, capacity, booked
    if day == today and datetime.now().time() >= max(s.end_time for s in schedules):
        return False, "Doctor ka aaj ka time khatam ho chuka hai.", schedules, capacity, booked
    if booked >= capacity:
        return False, "Is din ke saare tokens book ho chuke hain.", schedules, capacity, booked
    return True, "Booking available hai.", schedules, capacity, booked


def book_token(db: Session, patient: Patient, doctor_id: int, day: date, source: str) -> Appointment:
    # Doctor row lock: do log ek saath booking karein to token number na takraye (PostgreSQL)
    doctor = db.scalar(select(Doctor).where(Doctor.id == doctor_id).with_for_update())
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor nahi mila.")

    ok, message, _, _, _ = check_bookable(db, doctor, day)
    if not ok:
        raise HTTPException(status_code=400, detail=message)

    duplicate = db.scalar(
        select(Appointment.id).where(
            Appointment.patient_id == patient.id,
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == day,
            Appointment.status != "cancelled",
        )
    )
    if duplicate:
        raise HTTPException(status_code=400, detail="Aap ka is doctor ke saath is din ka token pehle se hai.")

    # Cancelled tokens bhi ginte hain, taake token number dobara use na ho
    last_token = db.scalar(
        select(func.max(Appointment.token_no)).where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == day,
        )
    ) or 0

    appt = Appointment(patient_id=patient.id, doctor_id=doctor_id, appointment_date=day,
                       token_no=last_token + 1, source=source, status="waiting")
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


def appointment_to_out(db: Session, appt: Appointment) -> dict:
    patient = db.get(Patient, appt.patient_id)
    doctor = db.get(Doctor, appt.doctor_id)
    doctor_user = db.get(User, doctor.user_id)
    return {
        "id": appt.id,
        "patient_id": appt.patient_id,
        "patient_name": patient.name,
        "doctor_id": appt.doctor_id,
        "doctor_name": doctor_user.name,
        "appointment_date": appt.appointment_date,
        "token_no": appt.token_no,
        "source": appt.source,
        "status": appt.status,
        "priority": appt.priority,
        "est_wait_minutes": appt.est_wait_minutes,
        "created_at": appt.created_at,
    }
