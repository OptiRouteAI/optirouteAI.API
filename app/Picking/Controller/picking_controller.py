from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.Picking.Schemas.picking_schema import GenerarPickingRequest, PickingSalidaSchema, PickingCabeceraSchema, PickingRutaAgrupadaSalidaSchema
from app.Picking.Services.picking_service import crear_picking, listar_picking_cabecera, obtener_ruta_picking, cancelar_pickings, completar_pickings  
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

@router.put("/{nro_picking}/cancelar", status_code=status.HTTP_200_OK)
def cancelar_picking_endpoint(nro_picking: str, db: Session = Depends(get_db)):
    """
    Cancela un picking específico.

    :param nro_picking: El número de picking a cancelar.
    :param db: La sesión de la base de datos.
    :return: Un mensaje indicando que el picking ha sido cancelado.
    """
    return cancelar_pickings(db, nro_picking)

@router.put("/{nro_picking}/completar", status_code=status.HTTP_200_OK)
def completar_picking_endpoint(nro_picking: str, db: Session = Depends(get_db)):
    """
    Completa un picking específico.

    :param nro_picking: El número de picking a completar.
    :param db: La sesión de la base de datos.
    :return: Un mensaje indicando que el picking ha sido completado.
    """
    return completar_pickings(db, nro_picking)