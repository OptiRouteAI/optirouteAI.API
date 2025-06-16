from fastapi import FastAPI
from app.database import engine, Base
from sqlalchemy import event
from app.PurchaseOrder.Controller.controllers import router as purchase_router
from app.Picking.Controller.picking_controller import router as picking_router
from app.Profile.Controller.user_controller import router as user_router
from app.Configuration.Controller.configuration_controller import router as configuration_router
from app.database import engine, Base, SessionLocal
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

print("Tablas registradas:", Base.metadata.tables.keys())

app = FastAPI(
    title="OptiRoute AI API",
    description="API for managing purchase orders in the OptiRoute AI system.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia esto por los dominios de tu frontend en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(purchase_router, prefix="/purchase")
app.include_router(picking_router, prefix="/picking")
app.include_router(user_router, prefix="/users")
app.include_router(configuration_router, prefix="/configuration")