from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_roles
from ..models import Department, User
from ..schemas import DepartmentCreate, DepartmentOut

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    """Saare departments (public)."""
    return db.scalars(select(Department).order_by(Department.name)).all()


@router.post("", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db),
                      _admin: User = Depends(require_roles("admin"))):
    name = data.name.strip()
    if db.scalar(select(Department).where(Department.name == name)):
        raise HTTPException(status_code=400, detail="Ye department pehle se maujood hai.")
    dept = Department(name=name)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept
