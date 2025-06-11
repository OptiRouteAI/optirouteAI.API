from sqlalchemy.orm import Session
from app.Configuration.Model.configuration import Configuracion

class ConfigurationService:
    def get_all_configuration(db: Session):
        return db.query(Configuracion).all()
    
    def set_configuration(cod_estrategia: str, db: Session):
        configuracion = db.query(Configuracion).filter(Configuracion.cod_estrategia == cod_estrategia).first()
    
       
        if not configuracion:
            return None
    
        if configuracion.flg_activo == 0:
            configuracion.flg_activo = 1
            # Buscar la otra estrategia activa y desactivarla (flg_activo = 0)
            otra_configuracion = db.query(Configuracion).filter(Configuracion.flg_activo == 1).first()
        if otra_configuracion and otra_configuracion.cod_estrategia != cod_estrategia:
            otra_configuracion.flg_activo = 0
            db.commit()
        else:
            configuracion.flg_activo = 0

        db.commit()
        db.refresh(configuracion)

        return configuracion