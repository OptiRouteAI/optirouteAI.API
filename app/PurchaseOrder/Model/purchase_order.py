from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Pedido(Base):
    __tablename__ = "pedido_cab"
    nro_pedido = Column("nro_pedido", String(20), primary_key=True, nullable=False)  # Sin auto_increment
    cliente = Column(String(100), nullable=False)  # Es opcional según tu descripción
    direccion = Column(String(255), nullable=False)
    fecha_pedido = Column(DateTime, default=datetime.now)

    detalles = relationship("PedidoDet", back_populates="pedido", cascade="all, delete-orphan")


class PedidoDet(Base):
    __tablename__ = "pedido_det"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nro_pedido = Column(Integer, ForeignKey("pedido_cab.nro_pedido", ondelete="CASCADE"), nullable=False)
    cod_articulo = Column(String(50), nullable=False)
    descripcion = Column(String(255), nullable=False)
    cantidad = Column(Integer, nullable=False)
    UM = Column(String(3), nullable=False)

    pedido = relationship("Pedido", back_populates="detalles")
