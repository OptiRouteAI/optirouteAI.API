from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.Picking.Schemas.picking_schema import GenerarPickingRequest, PickingSalidaSchema, PickingCabeceraSchema, PickingRutaAgrupadaSalidaSchema
from app.Picking.Services.picking_service import crear_picking, listar_picking_cabecera, obtener_ruta_picking
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

@router.get("/ruta/{nro_picking}", response_model=PickingRutaAgrupadaSalidaSchema)
def obtener_rutas(nro_picking: str, db: Session = Depends(get_db)):
    return obtener_ruta_picking(db, nro_picking)