from app.PurchaseOrder.Implementation import purchase_imp
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.PurchaseOrder.Model.purchase_order import Pedido
from datetime import date

def procesar_nuevo_pedido(db: Session, nro_pedido: int, cliente: str, direccion: str, detalles: list[dict]):
    return purchase_imp.crear_pedido(db, nro_pedido, cliente, direccion, detalles)

def obtener_pedidos(db: Session):
    return purchase_imp.listar_pedidos(db)

def filtrar_pedidos(db: Session, nro_pedido: str = None, cliente: str = None, fecha: date = None):
    filtros = []

    if nro_pedido:
        filtros.append(Pedido.nro_pedido.ilike(f"%{nro_pedido}%"))
    if cliente:
        filtros.append(Pedido.cliente.ilike(f"%{cliente}%"))
    if fecha:
        filtros.append(Pedido.fecha_pedido == fecha)

    return db.query(Pedido).filter(and_(*filtros)).all()

def obtener_detalles_pedido(db: Session, nro_pedido: str):
    from app.PurchaseOrder.Implementation.purchase_imp import obtener_detalles_por_pedido
    return obtener_detalles_por_pedido(db, nro_pedido)
