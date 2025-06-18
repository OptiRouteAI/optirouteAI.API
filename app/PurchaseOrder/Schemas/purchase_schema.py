from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class PedidoDetEntradaSchema(BaseModel):
    cod_articulo: str
    descripcion: str
    cantidad: int
    UM: str  # Unidad de medida (ej. UND, CJ)

class PedidoEntradaSchema(BaseModel):
    nro_pedido: str
    cliente: str
    direccion: str
    detalles: List[PedidoDetEntradaSchema]


class PedidoDetSalidaSchema(BaseModel):
    cod_articulo: str
    descripcion: str
    cantidad: int
    UM: str

class PedidoSalidaSchema(BaseModel):
    nro_pedido: str
    cliente: str
    direccion: str
    fecha_pedido: date
    detalles: List[PedidoDetSalidaSchema]

    @classmethod
    def from_orm(cls, pedido):
        return cls(
            nro_pedido=pedido.nro_pedido,
            cliente=pedido.cliente,
            direccion=pedido.direccion,
            fecha_pedido=pedido.fecha_pedido.date(),
            detalles=[
                PedidoDetSalidaSchema(
                    cod_articulo=d.cod_articulo,
                    descripcion=d.descripcion,
                    cantidad=d.cantidad,
                    UM=d.UM
                ) for d in pedido.detalles
            ]
        )


class PedidoFiltroSchema(BaseModel):
    nro_pedido: Optional[str] = None
    cliente: Optional[str] = None
    fecha: Optional[date] = None
    estado: Optional[str] = None