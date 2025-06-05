from app.PurchaseOrder.Implementation import purchase_imp  # ✅ Corrección aquí
from sqlalchemy.orm import Session

def procesar_nuevo_pedido(db: Session, nro_pedido: int, cliente: str, direccion: str, detalles: list[dict]):
    return purchase_imp.crear_pedido(db, nro_pedido, cliente, direccion, detalles)

def obtener_pedidos(db: Session):
    return purchase_imp.listar_pedidos(db)