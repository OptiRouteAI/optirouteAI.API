from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.PurchaseOrder.Schemas.purchase_schema import PedidoEntradaSchema, PedidoSalidaSchema
from app.PurchaseOrder.Services.purchase_service import procesar_nuevo_pedido, obtener_pedidos

router = APIRouter(prefix="/purchase-order", tags=["Purchase Order"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PedidoSalidaSchema)
def crear_pedido(
    pedido: PedidoEntradaSchema,
    db: Session = Depends(get_db)
):
    nuevo_pedido = procesar_nuevo_pedido(
        db,
        pedido.nro_pedido,   #ahora se incluye el nro_pedido
        pedido.cliente,
        pedido.direccion,
        [d.dict() for d in pedido.detalles]
    )
    return PedidoSalidaSchema.from_orm(nuevo_pedido)

@router.get("/", response_model=list[PedidoSalidaSchema])
def listar_pedidos(db: Session = Depends(get_db)):
    pedidos = obtener_pedidos(db)
    return [PedidoSalidaSchema.from_orm(p) for p in pedidos]
