from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from app.Picking.Model.picking_order import PickingCab, PickingDet
from app.PurchaseOrder.Model.purchase_order import PedidoDet
from app.Inventory.Model.saldo_ubicacion import SaldoUbicacion
from sqlalchemy import select
import uuid

def generar_codigo_picking(db: Session) -> str:
    ultimo = db.query(PickingCab).order_by(PickingCab.nro_picking.desc()).first()
    if not ultimo:
        return "PK0000001"
    ultimo_num = int(ultimo.nro_picking.replace("PK", ""))
    return f"PK{ultimo_num + 1:07d}"

def generar_picking_tradicional(db: Session, pedidos: list[str]) -> PickingCab:
    # Validar que los pedidos no estén ya en un picking activo
    for nro_pedido in pedidos:
        picking_existente = db.query(PickingDet).join(PickingCab).filter(
            PickingDet.nro_pedido == nro_pedido,
            PickingCab.estado == "EP"  # Solo bloqueamos si está en proceso
        ).first()
        if picking_existente:
            raise HTTPException(
                status_code=400,
                detail=f"El pedido {nro_pedido} ya está asociado a un picking en proceso."
            )

    nro_picking = generar_codigo_picking(db)
    nuevo_picking = PickingCab(
        nro_picking=nro_picking,
        fecha_generacion=datetime.utcnow(),
        estado="EP"
    )
    db.add(nuevo_picking)
    db.flush()

    for nro_pedido in pedidos:
        detalles = db.query(PedidoDet).filter(PedidoDet.nro_pedido == nro_pedido).all()

        if not detalles:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron detalles para el pedido {nro_pedido}"
            )

        for det in detalles:
            cantidad_restante = det.cantidad

            ubicaciones = db.query(SaldoUbicacion).filter(
                SaldoUbicacion.cod_articulo == det.cod_articulo,
                SaldoUbicacion.um == det.UM,
                SaldoUbicacion.cantidad > 0
            ).order_by(SaldoUbicacion.cantidad.desc()).all()

            if not ubicaciones:
                raise HTTPException(
                    status_code=404,
                    detail=f"No hay ubicaciones con stock para el artículo {det.cod_articulo} con UM {det.UM}"
                )

            for ubic in ubicaciones:
                if cantidad_restante == 0:
                    break
                tomar = min(ubic.cantidad, cantidad_restante)

                picking_det = PickingDet(
                    nro_picking=nro_picking,
                    nro_pedido=nro_pedido,
                    cod_lpn=ubic.cod_lpn,
                    cantidad=tomar,
                    ubicacion=ubic.ubicacion,
                    um=det.UM
                )
                db.add(picking_det)

                ubic.cantidad_reservada += tomar
                ubic.cantidad -= tomar
                cantidad_restante -= tomar

            if cantidad_restante > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"No hay stock suficiente para el artículo {det.cod_articulo} con UM {det.UM}"
                )

    db.commit()
    db.refresh(nuevo_picking)
    return nuevo_picking

def obtener_picking_cabecera(db: Session):
    return db.query(
        PickingCab.nro_picking,
        PickingCab.fecha_generacion,
        PickingCab.estado
    ).order_by(PickingCab.fecha_generacion.desc()).all()