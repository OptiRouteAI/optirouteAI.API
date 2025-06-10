from sqlalchemy.orm import Session
from app.Profile.Model.User import User
from app.Profile.Schemas.user import UserCreate, UserUpdate
from fastapi import HTTPException, status

def create_user(db: Session, user: UserCreate):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = User(
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        password=user.password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username, User.password == password).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

def get_user_by_id(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def update_user(db: Session, user_id: int, user_update: UserUpdate):
    user = get_user_by_id(db, user_id)
    if user_update.first_name is not None:
        user.first_name = user_update.first_name
    if user_update.last_name is not None:
        user.last_name = user_update.last_name
    if user_update.password:
        user.password = user_update.password
    db.commit()
    db.refresh(user)
    return user
