from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import Appointment, Doctor, Patient, User
from ..schemas import AppointmentCreate, AppointmentOut, WalkInCreate
from ..services.booking import book_token, appointment_to_out

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book_online(data: AppointmentCreate, db: Session = Depends(get_db),
                user: User = Depends(require_roles("patient"))):
    """Patient ghar se doctor ka token book karta hai."""
    patient = db.scalar(select(Patient).where(Patient.user_id == user.id))
    if patient is None:
        raise HTTPException(status_code=400, detail="Patient profile nahi mila.")
    appt = book_token(db, patient, data.doctor_id, data.appointment_date, source="online")
    return appointment_to_out(db, appt)


@router.post("/walkin", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book_walkin(data: WalkInCreate, db: Session = Depends(get_db),
                _staff: User = Depends(require_roles("reception", "admin"))):
    """Reception walk-in patient ka token aaj ke liye banati hai."""
    if db.get(Doctor, data.doctor_id) is None:
        raise HTTPException(status_code=404, detail="Doctor nahi mila.")
    patient = Patient(user_id=None, name=data.name, age=data.age,
                      gender=data.gender, phone=data.phone)
    db.add(patient)
    db.flush()
    try:
        appt = book_token(db, patient, data.doctor_id, date.today(), source="walkin")
    except HTTPException:
        db.rollback()  # booking fail ho to patient bhi save na ho
        raise
    return appointment_to_out(db, appt)


@router.get("/my", response_model=list[AppointmentOut])
def my_appointments(db: Session = Depends(get_db), user: User = Depends(require_roles("patient"))):
    """Patient ke apne saare tokens (naye pehle)."""
    patient = db.scalar(select(Patient).where(Patient.user_id == user.id))
    if patient is None:
        return []
    appts = db.scalars(
        select(Appointment).where(Appointment.patient_id == patient.id)
        .order_by(Appointment.appointment_date.desc(), Appointment.token_no.desc())
    ).all()
    return [appointment_to_out(db, a) for a in appts]


@router.get("", response_model=list[AppointmentOut])
def list_appointments(doctor_id: int | None = Query(default=None),
                      day: date | None = Query(default=None, alias="date"),
                      db: Session = Depends(get_db),
                      user: User = Depends(require_roles("doctor", "reception", "admin"))):
    """Staff ke liye tokens ki list (default: aaj). Doctor sirf apne patients dekhta hai."""
    if user.role == "doctor":
        doctor = db.scalar(select(Doctor).where(Doctor.user_id == user.id))
        if doctor is None:
            raise HTTPException(status_code=404, detail="Aap ka doctor profile nahi bana.")
        doctor_id = doctor.id

    query = select(Appointment).where(Appointment.appointment_date == (day or date.today()))
    if doctor_id is not None:
        query = query.where(Appointment.doctor_id == doctor_id)
    appts = db.scalars(query.order_by(Appointment.doctor_id, Appointment.token_no)).all()
    return [appointment_to_out(db, a) for a in appts]


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    """Patient apna token cancel kar sakta hai; reception/admin kisi ka bhi."""
    appt = db.get(Appointment, appointment_id)
    if appt is None:
        raise HTTPException(status_code=404, detail="Appointment nahi mili.")

    if user.role == "patient":
        patient = db.get(Patient, appt.patient_id)
        if patient.user_id != user.id:
            raise HTTPException(status_code=403, detail="Ye aap ka token nahi hai.")
    elif user.role not in ("reception", "admin"):
        raise HTTPException(status_code=403, detail="Aap ko is kaam ki ijazat nahi hai.")

    if appt.status != "waiting":
        raise HTTPException(status_code=400, detail="Sirf 'waiting' token cancel ho sakta hai.")
    appt.status = "cancelled"
    db.commit()
    db.refresh(appt)
    return appointment_to_out(db, appt)
