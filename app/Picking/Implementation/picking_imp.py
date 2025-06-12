from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from app.Picking.Model.picking_order import PickingCab, PickingDet
from app.PurchaseOrder.Model.purchase_order import PedidoDet
from app.Inventory.Model.saldo_ubicacion import SaldoUbicacion
from sqlalchemy import select
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from collections import defaultdict
import re
from sqlalchemy.sql import case

def extract_rack_col_niv_seq(ubic):
    partes = ubic.ubicacion.split('.')
    rack = partes[2]
    columna = partes[3]
    nivel = int(partes[4])
    secuencia = getattr(ubic, "secuencia", 9999)
    return rack, columna, nivel, secuencia

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

def extract_number(value):
    match = re.search(r'\d+', value)
    if match:
        return int(match.group())
    return 0


def create_distance_matrix(locations):
    num_locations = len(locations)
    distance_matrix = [[0] * num_locations for _ in range(num_locations)]

    for i in range(num_locations):
        for j in range(num_locations):
            # Extraer y convertir los valores a enteros
            rack_i = extract_number(locations[i].ubicacion.split('.')[2])  # C0X
            rack_j = extract_number(locations[j].ubicacion.split('.')[2])

            columna_i = extract_number(locations[i].ubicacion.split('.')[3])  # 00X
            columna_j = extract_number(locations[j].ubicacion.split('.')[3])

            nivel_i = extract_number(locations[i].ubicacion.split('.')[4])  # 0X
            nivel_j = extract_number(locations[j].ubicacion.split('.')[4])

            # Penalizar más fuertemente las diferencias en racks y niveles
            rack_diff = abs(rack_i - rack_j) * 1000
            nivel_diff = abs(nivel_i - nivel_j) * 100

            # Las columnas deben seguir un orden ascendente
            columna_diff = abs(columna_i - columna_j) * 10

            # Penalizar más fuertemente las ubicaciones en niveles superiores
            nivel_penalty = nivel_diff * 1000 if nivel_i > 1 or nivel_j > 1 else 0

            # Ponderar las diferencias para priorizar el orden correcto
            distance_matrix[i][j] = rack_diff + nivel_diff + columna_diff + nivel_penalty

    return distance_matrix

def generar_picking_con_ia(db: Session, pedidos: list[str]) -> PickingCab:
    # Validar que los pedidos no estén ya en un picking activo
    for nro_pedido in pedidos:
        picking_existente = db.query(PickingDet).join(PickingCab).filter(
            PickingDet.nro_pedido == nro_pedido,
            PickingCab.estado == "EP"
        ).first()
        if picking_existente:
            raise HTTPException(
                status_code=400,
                detail=f"El pedido {nro_pedido} ya está asociado a un picking en proceso."
            )

    # Obtener el stock de las ubicaciones para todos los pedidos
    ubicaciones = []
    detalles_pedidos = []
    for nro_pedido in pedidos:
        detalles = db.query(PedidoDet).filter(PedidoDet.nro_pedido == nro_pedido).all()
        if not detalles:
            raise HTTPException(status_code=404, detail=f"No se encontraron detalles para el pedido {nro_pedido}")
        detalles_pedidos.extend(detalles)

        for det in detalles:
            ubicaciones.extend(db.query(SaldoUbicacion).filter(
                SaldoUbicacion.cod_articulo == det.cod_articulo,
                SaldoUbicacion.um == det.UM,
                SaldoUbicacion.cantidad > 0
            ).all())

    # Separar ubicaciones por nivel
    ubicaciones_nivel_1 = [ubic for ubic in ubicaciones if extract_number(ubic.ubicacion.split('.')[4]) == 1]
    ubicaciones_otros_niveles = [ubic for ubic in ubicaciones if extract_number(ubic.ubicacion.split('.')[4]) > 1]

    detalles_picking = []

    # Procesar ubicaciones del nivel 1
    for det in detalles_pedidos:
        cantidad_requerida = det.cantidad
        cantidad_asignada = 0

        for ubic in ubicaciones_nivel_1:
            if ubic.cod_articulo == det.cod_articulo and ubic.cantidad > 0:
                cantidad_a_asignar = min(ubic.cantidad, cantidad_requerida - cantidad_asignada)
                detalles_picking.append({
                    "nro_pedido": det.nro_pedido,
                    "cod_lpn": ubic.cod_lpn,
                    "cantidad": cantidad_a_asignar,
                    "ubicacion": ubic.ubicacion,
                    "um": ubic.um
                })
                ubic.cantidad_reservada += cantidad_a_asignar
                ubic.cantidad -= cantidad_a_asignar
                cantidad_asignada += cantidad_a_asignar
                if cantidad_asignada == cantidad_requerida:
                    break

    # Si no se ha completado la cantidad requerida, complementar con otras ubicaciones de otros niveles
    if cantidad_asignada < cantidad_requerida:
        # Agrupar ubicaciones por rack y columna
        ubicaciones_por_rack_columna = defaultdict(list)
        for ubic in ubicaciones_otros_niveles:
            rack = ubic.ubicacion.split('.')[2]
            columna = ubic.ubicacion.split('.')[3]
            ubicaciones_por_rack_columna[(rack, columna)].append(ubic)

        # Ordenar ubicaciones por rack y columna
        ubicaciones_ordenadas = sorted(ubicaciones_otros_niveles, key=lambda x: (
            x.ubicacion.split('.')[2],  # Rack
            extract_number(x.ubicacion.split('.')[3])  # Columna
        ))

        for det in detalles_pedidos:
            cantidad_requerida = det.cantidad
            cantidad_asignada = sum(detalle["cantidad"] for detalle in detalles_picking if detalle["nro_pedido"] == det.nro_pedido)

            for ubic in ubicaciones_ordenadas:
                if ubic.cod_articulo == det.cod_articulo and ubic.cantidad > 0:
                    cantidad_a_asignar = min(ubic.cantidad, cantidad_requerida - cantidad_asignada)
                    detalles_picking.append({
                        "nro_pedido": det.nro_pedido,
                        "cod_lpn": ubic.cod_lpn,
                        "cantidad": cantidad_a_asignar,
                        "ubicacion": ubic.ubicacion,
                        "um": ubic.um
                    })
                    ubic.cantidad_reservada += cantidad_a_asignar
                    ubic.cantidad -= cantidad_a_asignar
                    cantidad_asignada += cantidad_a_asignar
                    if cantidad_asignada == cantidad_requerida:
                        break

    # Crear el picking con los detalles asignados
    nro_picking = generar_codigo_picking(db)
    nuevo_picking = PickingCab(
        nro_picking=nro_picking,
        fecha_generacion=datetime.utcnow(),
        estado="EP"
    )
    db.add(nuevo_picking)

    for detalle in detalles_picking:
        picking_det = PickingDet(
            nro_picking=nro_picking,
            nro_pedido=detalle["nro_pedido"],
            cod_lpn=detalle["cod_lpn"],
            cantidad=detalle["cantidad"],
            ubicacion=detalle["ubicacion"],
            um=detalle["um"]
        )
        db.add(picking_det)

    db.commit()
    db.refresh(nuevo_picking)

    return nuevo_picking

def obtener_picking_cabecera(db: Session):
    return db.query(
        PickingCab.nro_picking,
        PickingCab.fecha_generacion,
        PickingCab.estado
    ).order_by(PickingCab.fecha_generacion.desc()).all()