from fastapi import FastAPI
from app.database import engine, Base
import app.PurchaseOrder.Model.purchase_order  
import app.Picking.Model.picking_order         
import app.Inventory.Model.saldo_ubicacion          

Base.metadata.create_all(bind=engine)

from app.PurchaseOrder.Controller.controllers import router as purchase_router
from app.Picking.Controller.picking_controller import router as picking_router

app = FastAPI(
    title="OptiRoute AI API",
    description="API for managing purchase orders in the OptiRoute AI system.",
    version="1.0.0"
)

app.include_router(purchase_router, prefix="/purchase")
app.include_router(picking_router, prefix="/picking")
