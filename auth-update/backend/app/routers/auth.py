from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User, Patient
from ..schemas import PatientRegister, UserOut, Token
from ..security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_patient(data: PatientRegister, db: Session = Depends(get_db)):
    """Naya patient account (User + Patient profile)."""
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=400, detail="Ye email pehle se registered hai.")

    user = User(name=data.name, email=email,
                password_hash=hash_password(data.password), role="patient")
    db.add(user)
    db.flush()  # user.id mil jati hai

    db.add(Patient(user_id=user.id, name=data.name, age=data.age,
                   gender=data.gender, phone=data.phone))
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login. Form me 'username' field me email likhein."""
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ya password galat hai.")
    token = create_access_token(user.id, user.role)
    return Token(access_token=token, role=user.role, name=user.name)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """Abhi login user kaun hai."""
    return current_user
