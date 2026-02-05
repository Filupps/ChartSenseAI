from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routes import router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(" Initializing database...")
    try:
        from app.db.database import init_db
        init_db()
        print(" Database initialized successfully")
    except Exception as e:
        print(f" Database initialization failed: {e}")
        print("   Make sure MySQL is running and database 'ChartSenseAI' exists")
    yield


app = FastAPI(
    title="ChartSenseAI",
    description="API for diagram analysis and algorithm extraction",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "ChartSenseAI API is running"}


@app.get("/api/health")
async def health():
    return {"status": "healthy"}
