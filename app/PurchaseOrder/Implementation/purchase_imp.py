from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.PurchaseOrder.Model.purchase_order import Pedido, PedidoDet

def crear_pedido(db: Session, nro_pedido: int, cliente: str, direccion: str, detalles: list[dict]):
    existe = db.query(Pedido).filter(Pedido.nro_pedido == nro_pedido).first()
    if existe:
        raise HTTPException(status_code=400, detail=f"El pedido con nro_pedido={nro_pedido} ya existe.")
    
    pedido = Pedido(nro_pedido=nro_pedido, cliente=cliente, direccion=direccion)
    db.add(pedido)
    db.flush()

    for i, det in enumerate(detalles, start=1):
        um = det["UM"].upper()
        if um not in ("CJ", "UND"):
            raise HTTPException(
                status_code=400,
                detail=f"Detalle #{i}: El campo 'UM' solo puede ser 'CJ' o 'UND'. Valor recibido: '{um}'"
            )

        pedido_det = PedidoDet(
            nro_pedido=pedido.nro_pedido,
            cod_articulo=det["cod_articulo"],
            descripcion=det.get("descripcion", ""),
            cantidad=det["cantidad"],
            UM=um
        )
        db.add(pedido_det)

    db.commit()
    db.refresh(pedido)
    return pedido
def listar_pedidos(db: Session):
    return db.query(Pedido).all()

def obtener_detalles_por_pedido(db: Session, nro_pedido: str):
    pedido = db.query(Pedido).filter(Pedido.nro_pedido == nro_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido con número {nro_pedido} no encontrado")
    
    return pedido.detalles  # devuelve solo la lista de detalles