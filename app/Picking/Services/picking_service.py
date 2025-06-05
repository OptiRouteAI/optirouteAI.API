from sqlalchemy.orm import Session
from app.Picking.Implementation.picking_imp import generar_picking_tradicional
from app.Picking.Model.picking_order import PickingCab

def crear_picking(db: Session, pedidos: list[str]):
    return generar_picking_tradicional(db, pedidos)


def listar_picking_cabecera(db: Session):
    return db.query(PickingCab).order_by(PickingCab.fecha_generacion.desc()).all()
