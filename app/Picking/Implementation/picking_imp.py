from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from app.Picking.Model.picking_order import PickingCab, PickingDet
from app.PurchaseOrder.Model.purchase_order import PedidoDet, Pedido
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
            PickingCab.estado == "EN PROCESO"  # Solo bloqueamos si está en proceso
        ).first()
        if picking_existente:
            raise HTTPException(
                status_code=400,
                detail=f"El pedido {nro_pedido} ya está asociado a un picking en proceso."
            )

    # Generar un nuevo código de picking
    nro_picking = generar_codigo_picking(db)
    nuevo_picking = PickingCab(
        nro_picking=nro_picking,
        fecha_generacion=datetime.utcnow(),
        estado="PENDIENTE"
    )
    db.add(nuevo_picking)
    db.flush()

    # Actualizar el estado de los pedidos a "EN PICKING"
    for nro_pedido in pedidos:
        pedido = db.query(Pedido).filter(Pedido.nro_pedido == nro_pedido).first()
        if pedido:
            pedido.estado = "EN PICKING"
            db.add(pedido)

    # Asignar ubicaciones a los artículos en los pedidos
    for nro_pedido in pedidos:
        detalles = db.query(PedidoDet).filter(PedidoDet.nro_pedido == nro_pedido).all()

        if not detalles:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron detalles para el pedido {nro_pedido}"
            )

        for det in detalles:
            cantidad_restante = det.cantidad

            # Obtener ubicaciones disponibles para el artículo
            ubicaciones = db.query(SaldoUbicacion).filter(
                SaldoUbicacion.cod_articulo == det.cod_articulo,
                SaldoUbicacion.um == det.UM,
                SaldoUbicacion.cantidad > 0
            ).all()

            if not ubicaciones:
                raise HTTPException(
                    status_code=404,
                    detail=f"No hay ubicaciones con stock para el artículo {det.cod_articulo} con UM {det.UM}"
                )

            # Asignar ubicaciones sin ningún criterio específico
            for ubic in ubicaciones:
                if cantidad_restante <= 0:
                    break

                cantidad_a_tomar = min(ubic.cantidad, cantidad_restante)

                picking_det = PickingDet(
                    nro_picking=nro_picking,
                    nro_pedido=nro_pedido,
                    cod_lpn=ubic.cod_lpn,
                    cantidad=cantidad_a_tomar,
                    ubicacion=ubic.ubicacion,
                    um=det.UM
                )
                db.add(picking_det)

                # Actualizar la cantidad y la cantidad reservada en la ubicación
                ubic.cantidad -= cantidad_a_tomar
                ubic.cantidad_reservada += cantidad_a_tomar
                cantidad_restante -= cantidad_a_tomar

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
            PickingCab.estado == "PENDIENTE"  # Solo bloqueamos si está en proceso
        ).first()
        if picking_existente:
            raise HTTPException(
                status_code=400,
                detail=f"El pedido {nro_pedido} ya está asociado a un picking en proceso."
            )

    # Actualizar el estado de los pedidos a "EN PICKING"
    for nro_pedido in pedidos:
        pedido = db.query(Pedido).filter(Pedido.nro_pedido == nro_pedido).first()
        if pedido:
            pedido.estado = "EN PICKING"
            db.add(pedido)

    # Obtener el stock de las ubicaciones para todos los pedidos
    detalles_pedidos = []
    ubicaciones_por_articulo = defaultdict(list)

    for nro_pedido in pedidos:
        detalles = db.query(PedidoDet).filter(PedidoDet.nro_pedido == nro_pedido).all()
        if not detalles:
            raise HTTPException(status_code=404, detail=f"No se encontraron detalles para el pedido {nro_pedido}")
        detalles_pedidos.extend(detalles)

        for det in detalles:
            ubicaciones = db.query(SaldoUbicacion).filter(
                SaldoUbicacion.cod_articulo == det.cod_articulo,
                SaldoUbicacion.um == det.UM,
                SaldoUbicacion.cantidad > 0
            ).all()
            ubicaciones_por_articulo[det.cod_articulo].extend(ubicaciones)

    detalles_picking = []

    # Procesar ubicaciones para cada artículo
    for det in detalles_pedidos:
        cantidad_requerida = det.cantidad
        cantidad_asignada = 0

        # Obtener ubicaciones para el artículo actual
        ubicaciones_articulo = ubicaciones_por_articulo.get(det.cod_articulo, [])

        # Separar ubicaciones por nivel
        ubicaciones_nivel_1 = [ubic for ubic in ubicaciones_articulo if extract_number(ubic.ubicacion.split('.')[4]) == 1]
        ubicaciones_otros_niveles = [ubic for ubic in ubicaciones_articulo if extract_number(ubic.ubicacion.split('.')[4]) > 1]

        # Procesar ubicaciones del nivel 1
        for ubic in ubicaciones_nivel_1:
            if ubic.cantidad > 0 and cantidad_asignada < cantidad_requerida:
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
            # Ordenar ubicaciones de otros niveles por rack y columna
            ubicaciones_ordenadas = sorted(ubicaciones_otros_niveles, key=lambda x: (
                x.ubicacion.split('.')[2],  # Rack
                extract_number(x.ubicacion.split('.')[3])  # Columna
            ))

            for ubic in ubicaciones_ordenadas:
                if ubic.cantidad > 0 and cantidad_asignada < cantidad_requerida:
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
        estado="PENDIENTE"  # Estado inicial del picking
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

def cancelar_picking(db: Session, nro_picking: str) -> dict:
    """
    Cancela un picking específico, libera las cantidades reservadas en las ubicaciones
    y actualiza el estado de los pedidos asociados a "INGRESADO".

    :param db: La sesión de la base de datos.
    :param nro_picking: El número de picking a cancelar.
    :return: Un diccionario con un mensaje indicando que el picking ha sido cancelado.
    """
    # Buscar el picking a cancelar
    picking = db.query(PickingCab).filter(PickingCab.nro_picking == nro_picking).first()
    if not picking:
        raise HTTPException(status_code=404, detail="Picking no encontrado.")

    # Verificar si el picking está en un estado que no permite cancelación
    if picking.estado == "EN PROCESO":
        raise HTTPException(
            status_code=400,
            detail="No se puede cancelar el picking porque está en proceso."
        )

    # Actualizar el estado del picking a "CANCELADO"
    picking.estado = "CANCELADO"

    # Obtener todos los detalles del picking para liberar cantidades y actualizar pedidos
    detalles_picking = db.query(PickingDet).filter(PickingDet.nro_picking == nro_picking).all()

    # Liberar las cantidades reservadas en las ubicaciones
    for detalle in detalles_picking:
        ubicacion = db.query(SaldoUbicacion).filter(
            SaldoUbicacion.cod_lpn == detalle.cod_lpn,
            SaldoUbicacion.ubicacion == detalle.ubicacion
        ).first()
        if ubicacion:
            ubicacion.cantidad += detalle.cantidad
            ubicacion.cantidad_reservada -= detalle.cantidad

    # Actualizar el estado de los pedidos asociados a "INGRESADO"
    for detalle in detalles_picking:
        pedido = db.query(Pedido).filter(Pedido.nro_pedido == detalle.nro_pedido).first()
        if pedido:
            pedido.estado = "INGRESADO"
            db.add(pedido)

    db.commit()
    return {"mensaje": f"El picking {nro_picking} ha sido cancelado exitosamente."}