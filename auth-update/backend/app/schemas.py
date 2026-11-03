from typing import Literal
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
