# src/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.Models import TableModels
from src.Config.settings import get_settings
from src.Config.database import init_database, create_db_and_tables, close_database
from src.API.Routes.auth_routes import router as authRouter

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Starting up application...")
    init_database()
    create_db_and_tables()
    yield
    # Shutdown
    print("Shutting down application...")
    close_database()

# Initialize the FastAPI app with lifespan
app = FastAPI(
    title=settings.APP_NAME, 
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,  
    allow_methods=["*"],     
    allow_headers=["*"],     
)

app.include_router(authRouter, prefix="/api/auth", tags=["Authentication"])

@app.get("/")
def root_route():
    return {"message": "Hello, World!"}
