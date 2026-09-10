from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, budget, goals, decision, tips
from database import Base, engine

from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("DB initialiser avec succes")
    yield

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Backend API pour Ecobudget V1",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentification"])
app.include_router(budget.router, prefix="/api/v1/budget", tags=["Budget & Transactions"])
app.include_router(goals.router, prefix="/api/v1/goals", tags=["Objectifs d'Épargne"])
app.include_router(decision.router, prefix="/api/v1/decision", tags=["Assistant de Décision"])
app.include_router(tips.router, prefix="/api/v1/tips", tags=["Conseils Financiers"])

@app.get("/")
def read_root():
    return {"message": "API Ecobudget opérationnelle"}