from sqlalchemy import Column, String, Integer, CheckConstraint
from app.database import Base

class Configuracion(Base):
    __tablename__ = 'configuracion'

    cod_estrategia = Column(String(10), primary_key=True)
    nombre = Column(String(50), nullable=False)
    descripcion = Column(String(255))
    flg_activo = Column(Integer, CheckConstraint('flg_activo IN (0, 1)'), default=0)