from sqlalchemy import Column, String, Integer
from app.database import Base

class SaldoUbicacion(Base):
    __tablename__ = "saldo_ubicacion"

    id_saldo_ubic = Column(Integer, primary_key=True, autoincrement=True)
    cod_articulo = Column(String(50), nullable=False)
    ubicacion = Column(String(50), nullable=False)
    rack = Column(String(50), nullable=False)
    columna = Column(String(50), nullable=False)
    nivel = Column(String(50), nullable=False)
    um = Column(String(3), nullable=False)
    cantidad = Column(Integer, nullable=False, default=0)
    cantidad_reservada = Column(Integer, nullable=False, default=0)
    cod_lpn = Column(String(50),nullable=False)
    secuencia = Column(Integer, nullable=False, default=0)