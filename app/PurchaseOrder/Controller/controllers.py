from fastapi import APIRouter, Depends, status, Query
from datetime import date
from sqlalchemy.orm import Session
from app.database import get_db
from app.PurchaseOrder.Schemas.purchase_schema import PedidoEntradaSchema, PedidoSalidaSchema, PedidoFiltroSchema, PedidoDetSalidaSchema
from app.PurchaseOrder.Services.purchase_service import procesar_nuevo_pedido, obtener_pedidos, filtrar_pedidos, obtener_detalles_pedido
from typing import List, Optional

router = APIRouter(prefix="/purchase-order", tags=["Purchase Order"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PedidoSalidaSchema)
def crear_pedido(
    pedido: PedidoEntradaSchema,
    db: Session = Depends(get_db)
):
    nuevo_pedido = procesar_nuevo_pedido(
        db,
        pedido.nro_pedido,
        pedido.cliente,
        pedido.direccion,
        [d.dict() for d in pedido.detalles]
    )
    return PedidoSalidaSchema.from_orm(nuevo_pedido)

@router.get("/", response_model=list[PedidoSalidaSchema])
def listar_pedidos(db: Session = Depends(get_db)):
    pedidos = obtener_pedidos(db)
    return [PedidoSalidaSchema.from_orm(p) for p in pedidos]

@router.get("/filtrar", response_model=List[PedidoFiltroSchema])  # puedes cambiar a un schema de salida si quieres
def buscar_pedidos(
    nro_pedido: Optional[str] = Query(None),
    cliente: Optional[str] = Query(None),
    fecha: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    return filtrar_pedidos(db, nro_pedido, cliente, fecha)

@router.get("/{nro_pedido}/details", response_model=List[PedidoDetSalidaSchema])
def obtener_detalles_de_pedido(nro_pedido: str, db: Session = Depends(get_db)):
    detalles = obtener_detalles_pedido(db, nro_pedido)
    return [
        PedidoDetSalidaSchema(
            cod_articulo=d.cod_articulo,
            descripcion=d.descripcion,
            cantidad=d.cantidad,
            UM=d.UM
        )
        for d in detalles
    ]