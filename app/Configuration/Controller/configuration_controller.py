from fastapi import APIRouter
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.Configuration.Services.configuration_service import ConfigurationService
from app.Configuration.Schemas.configuration_schema import ConfiguracionSchema
from app.database import SessionLocal

router = APIRouter(prefix="/configuration", tags=["Configuration"])

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint para obtener todas las configuraciones
@router.get("/configuracion/", response_model=list[ConfiguracionSchema])
def obtener_configuraciones(db: Session = Depends(get_db)):
    configuraciones = ConfigurationService.get_all_configuration(db)
    return configuraciones

# Endpoint para actualizar flg_activo (set_configuration)
@router.put("/configuracion/{cod_estrategia}/set", response_model=ConfiguracionSchema)
def set_configuration(cod_estrategia: str, db: Session = Depends(get_db)):
    configuracion = ConfigurationService.set_configuration(cod_estrategia, db)
    
    if not configuracion:
        raise HTTPException(status_code=404, detail="Estrategia no encontrada")

    return configuracion