from sqlalchemy.orm import Session
from app.Picking.Implementation.picking_imp import generar_picking_tradicional, generar_picking_con_ia
from app.Picking.Model.picking_order import PickingCab
from app.Configuration.Model.configuration import Configuracion
from fastapi import HTTPException

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
