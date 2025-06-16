from sqlalchemy.orm import Session
from app.Picking.Implementation.picking_imp import generar_picking_tradicional, generar_picking_con_ia
from app.Picking.Model.picking_order import PickingCab
from app.Configuration.Model.configuration import Configuracion
from app.Picking.Schemas.picking_schema import PickingRutaCabeceraSchema, PickingRutaDetalleSchema, PickingRutaAgrupadaSalidaSchema
from sqlalchemy import text
from fastapi import HTTPException
from collections import defaultdict

def obtener_configuracion_activa(db: Session):
    return db.query(Configuracion).filter(Configuracion.flg_activo == 1).first()

def crear_picking(db: Session, pedidos: list[str]):
    configuracion_activa = obtener_configuracion_activa(db)

    if not configuracion_activa:
        raise HTTPException(status_code=404, detail="No se encontró una configuración activa.")

    if configuracion_activa.cod_estrategia == "PK_TRAD":
        return generar_picking_tradicional(db, pedidos)
    elif configuracion_activa.cod_estrategia == "PK_MOD":
        return generar_picking_con_ia(db, pedidos)
    else:
        raise HTTPException(status_code=400, detail="Estrategia de picking no reconocida.")
    
def listar_picking_cabecera(db: Session):
    return db.query(PickingCab).order_by(PickingCab.fecha_generacion.desc()).all()

def obtener_ruta_picking(db: Session, nro_picking: str) -> PickingRutaAgrupadaSalidaSchema:
    query = text("""
       SELECT DISTINCT
            C.NRO_PEDIDO,
            C.CLIENTE,
            D.COD_ARTICULO,
            D.DESCRIPCION,
            PD.CANTIDAD,
            PD.UM,
            PD.UBICACION,
            S.NIVEL
        FROM picking_det PD
        JOIN pedido_cab C ON PD.NRO_PEDIDO = C.NRO_PEDIDO
        JOIN pedido_det D ON D.NRO_PEDIDO = PD.NRO_PEDIDO
        JOIN saldo_ubicacion S ON D.COD_ARTICULO = S.COD_ARTICULO AND PD.UBICACION = S.UBICACION AND S.COD_LPN = PD.COD_LPN
        WHERE PD.NRO_PICKING = :nro_picking
        ORDER BY S.NIVEL ASC
    """)
    resultado = db.execute(query, {"nro_picking": nro_picking}).fetchall()

    agrupado = defaultdict(list)

    for row in resultado:
        nro_pedido, cliente, cod_articulo, descripcion, cantidad, um, ubicacion, nivel = row
        agrupado[(nro_pedido, cliente)].append(PickingRutaDetalleSchema(
            cod_articulo=cod_articulo,
            descripcion=descripcion,
            cantidad=cantidad,
            um=um,
            ubicacion=ubicacion,
        ))

    rutas = [
        PickingRutaCabeceraSchema(
            nro_pedido=nro_pedido,
            cliente=cliente,
            detalles=detalles
        )
        for (nro_pedido, cliente), detalles in agrupado.items()
    ]

    return PickingRutaAgrupadaSalidaSchema(rutas=rutas)