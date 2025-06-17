from sqlalchemy.orm import Session
from app.Picking.Implementation.picking_imp import generar_picking_tradicional, generar_picking_con_ia, cancelar_picking
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

def extract_number(s):
    import re
    match = re.search(r'\d+', s)
    if match:
        return int(match.group())
    return 0

def obtener_ruta_picking(db: Session, nro_picking: str) -> PickingRutaAgrupadaSalidaSchema:
    # Actualizar el estado del picking a "EN PROCESO"
    update_query = text("""
        UPDATE picking_cab
        SET estado = 'EN PROCESO'
        WHERE nro_picking = :nro_picking
    """)
    db.execute(update_query, {"nro_picking": nro_picking})
    db.commit()

    # Consulta para obtener la estrategia activa
    estrategia_query = text("SELECT cod_estrategia FROM configuracion WHERE flg_activo = 1")
    estrategia_result = db.execute(estrategia_query).fetchone()

    # Determinar si el picking es de tipo IA
    es_picking_ia = estrategia_result and estrategia_result[0] == "PK_MOD"

    # Consulta SQL para obtener los datos sin ordenamiento específico
    query = text("""
        SELECT DISTINCT
            C.NRO_PEDIDO,
            C.CLIENTE,
            S.COD_ARTICULO,
            D.DESCRIPCION,
            PD.CANTIDAD,
            PD.UM,
            PD.UBICACION
        FROM picking_det PD
        JOIN pedido_cab C ON PD.NRO_PEDIDO = C.NRO_PEDIDO
        JOIN pedido_det D ON D.NRO_PEDIDO = PD.NRO_PEDIDO
        JOIN saldo_ubicacion S ON D.COD_ARTICULO = S.COD_ARTICULO AND PD.UBICACION = S.UBICACION AND S.COD_LPN = PD.COD_LPN
        WHERE PD.NRO_PICKING = :nro_picking
    """)

    resultado = db.execute(query, {"nro_picking": nro_picking}).fetchall()

    if es_picking_ia:
        # Separar las ubicaciones por nivel
        ubicaciones_nivel_1 = [row for row in resultado if extract_number(row[6].split('.')[4]) == 1]
        ubicaciones_otros_niveles = [row for row in resultado if extract_number(row[6].split('.')[4]) > 1]

        # Ordenar ubicaciones de otros niveles por rack y columna
        ubicaciones_ordenadas = sorted(ubicaciones_otros_niveles, key=lambda x: (
            x[6].split('.')[1],  # Rack
            extract_number(x[6].split('.')[2])  # Columna
        ))

        # Combinar las ubicaciones de nivel 1 y las ubicaciones ordenadas de otros niveles
        resultado_ordenado = ubicaciones_nivel_1 + ubicaciones_ordenadas
    else:
        # Si no es un picking de IA, usar el resultado sin ordenar
        resultado_ordenado = resultado

    agrupado = defaultdict(list)

    for row in resultado_ordenado:
        nro_pedido, cliente, cod_articulo, descripcion, cantidad, um, ubicacion = row
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

def cancelar_pickings(db: Session, nro_picking: str):
    """
    Cancela un picking específico.

    :param db: La sesión de la base de datos.
    :param nro_picking: El número de picking a cancelar.
    :return: Un mensaje indicando que el picking ha sido cancelado.
    """
    return cancelar_picking(db, nro_picking)