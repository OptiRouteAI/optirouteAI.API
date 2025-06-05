from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.PurchaseOrder.Model.purchase_order import Pedido  # Para la relación

import enum

# Definimos enum para estado
class EstadoPickingEnum(str, enum.Enum):
    EN_PROCESO = "EP"
    COMPLETO = "PC"

class PickingCab(Base):
    __tablename__ = "picking_cab"

    nro_picking = Column(String(20), primary_key=True, index=True)  # PK con formato PK0000001
    fecha_generacion = Column(DateTime, default=datetime.now, nullable=False)
    estado = Column(String(2), nullable=False, default="EP")

    detalles = relationship("PickingDet", back_populates="picking", cascade="all, delete")

class PickingDet(Base):
    __tablename__ = "picking_det"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nro_picking = Column(String(20), ForeignKey("picking_cab.nro_picking", ondelete="CASCADE"), nullable=False)
    nro_pedido = Column(String(20), ForeignKey("pedido_cab.nro_pedido", ondelete="RESTRICT"), nullable=False)
    cod_lpn = Column(String(50), nullable=False)
    cantidad = Column(Integer, nullable=False)
    ubicacion = Column(String(50), nullable=False)
    um = Column(String(3), nullable=False)

    # Relaciones
    picking = relationship("PickingCab", back_populates="detalles")
    pedido = relationship("Pedido", backref="pickings")
