from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_roles
from ..models import User
from ..schemas import StaffCreate, UserOut
from ..security import hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_staff(data: StaffCreate, db: Session = Depends(get_db),
                 _admin: User = Depends(require_roles("admin"))):
    """Admin doctor / reception / admin ka account banata hai."""
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=400, detail="Ye email pehle se registered hai.")
    user = User(name=data.name, email=email,
                password_hash=hash_password(data.password), role=data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db),
               _admin: User = Depends(require_roles("admin"))):
    """Admin saare users ki list dekhta hai."""
    return db.scalars(select(User).order_by(User.id)).all()
