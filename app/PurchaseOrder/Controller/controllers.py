from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.Picking.Schemas.picking_schema import GenerarPickingRequest, PickingSalidaSchema, PickingCabeceraSchema
from app.Picking.Services.picking_service import crear_picking, listar_picking_cabecera
from typing import List

router = APIRouter(prefix="/picking", tags=["Picking"])

@router.post("/", response_model=PickingSalidaSchema, status_code=status.HTTP_201_CREATED)
def generar_picking(
    request: GenerarPickingRequest,
    db: Session = Depends(get_db)
):
    nro_pedidos = [p.nro_pedido for p in request.pedidos]
    picking = crear_picking(db, nro_pedidos)

    return PickingSalidaSchema(
        nro_picking=picking.nro_picking,
        fecha_generacion=picking.fecha_generacion.isoformat(),
        estado=picking.estado,
        detalles=[
            {
                "cod_lpn": d.cod_lpn,
                "cantidad": d.cantidad,
                "ubicacion": d.ubicacion,
                "um": d.um
            }
            for d in picking.detalles
        ]
    )

@router.get("/", response_model=List[PickingCabeceraSchema])
def obtener_todos_los_pickings(db: Session = Depends(get_db)):
    return listar_picking_cabecera(db)
