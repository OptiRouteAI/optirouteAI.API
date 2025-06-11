from typing import Optional
from pydantic import BaseModel

class ConfiguracionSchema(BaseModel):
    cod_estrategia: str
    nombre: str
    descripcion: Optional[str] = None
    flg_activo: int

    class Config:
        orm_mode = True