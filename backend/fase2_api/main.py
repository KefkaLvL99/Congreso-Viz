# ============================================================
# main.py
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from scheduler import iniciar_scheduler
from routers import senadores, comisiones, diputados, votaciones, parlamentarios
from routers import resumen
from routers import busqueda
from routers import gastos
from routers import leyes

scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    scheduler = iniciar_scheduler()
    yield
    if scheduler:
        scheduler.shutdown()

app = FastAPI(
    title="Congreso Viz Chile API",
    description="API para datos del Congreso Nacional de Chile",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(senadores.router,     prefix="/senadores",     tags=["Senadores"])
app.include_router(comisiones.router,    prefix="/comisiones",    tags=["Comisiones"])
app.include_router(diputados.router,     prefix="/diputados",     tags=["Diputados"])
app.include_router(votaciones.router,    prefix="/votaciones",    tags=["Votaciones"])
app.include_router(parlamentarios.router,prefix="/parlamentarios",tags=["Parlamentarios"])
app.include_router(resumen.router,       prefix="/resumen",       tags=["Resumen IA"])
app.include_router(busqueda.router, prefix="/busqueda", tags=["Búsqueda"])
app.include_router(gastos.router, prefix="/gastos", tags=["Gastos"])
app.include_router(leyes.router, prefix="/leyes", tags=["Leyes"])
@app.get("/")
def root():
    return {"status": "ok", "mensaje": "Congreso Viz Chile API"}
