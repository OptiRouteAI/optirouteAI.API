from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.Profile.Schemas.user import UserCreate, UserUpdate, UserOut, UserLogin
from app.Profile.services import user_services
from app.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return user_services.create_user(db, user)

@router.post("/authenticate", response_model=UserOut)
def authenticate_user(user_login: UserLogin, db: Session = Depends(get_db)):
    return user_services.authenticate_user(db, user_login.username, user_login.password)

@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    return user_services.get_user_by_id(db, user_id)

@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    return user_services.update_user(db, user_id, user_update)
