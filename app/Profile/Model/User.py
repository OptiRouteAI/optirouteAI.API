# app/Profile/Model/User.py

from sqlalchemy import Column, Integer, String
from app.database import Base  # ¡Usa el mismo Base que en main.py!

class User(Base):
    __tablename__ = "users"  # Este nombre debe ser EXACTAMENTE "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    password = Column(String(128), nullable=False)
