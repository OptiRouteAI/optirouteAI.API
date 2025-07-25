from pydantic import BaseModel
from typing import List
from datetime import datetime

class PickingDetalleEntradaSchema(BaseModel):
    nro_pedido: str

class GenerarPickingRequest(BaseModel):
    pedidos: List[PickingDetalleEntradaSchema]

class PickingDetSalidaSchema(BaseModel):
    cod_lpn: str
    cantidad: int
    ubicacion: str
    um: str

class PickingSalidaSchema(BaseModel):
    nro_picking: str
    fecha_generacion: datetime
    estado: str
    detalles: List[PickingDetSalidaSchema]

class PickingCabeceraSchema(BaseModel):
    nro_picking: str
    fecha_generacion: datetime
    estado: str

class PickingRutaDetalleSchema(BaseModel):
    cod_articulo: str
    descripcion: str
    cantidad: int
    um: str
    ubicacion: str

class PickingRutaCabeceraSchema(BaseModel):
    nro_pedido: str
    cliente: str
    detalles: List[PickingRutaDetalleSchema]

class PickingRutaAgrupadaSalidaSchema(BaseModel):
    rutas: List[PickingRutaCabeceraSchema]