# src/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.Models import TableModels
from src.Config.settings import get_settings
from src.Config.database import init_database, create_db_and_tables, close_database, getSessionLocal
from src.API.Routes.auth_routes import router as authRouter
from src.API.Routes.user_routes import router as userRouter
from src.API.Routes.game_routers import router as gameRouter 
from src.Services.game_generator import generate_initial_games

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Starting up application...")
    init_database()
    create_db_and_tables()
    dbSessonLocal = getSessionLocal()
    db : Session = dbSessonLocal()
    try:
        generate_initial_games(db)
    finally:
        db.close()
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
app.include_router(userRouter, prefix="/api/user", tags=["User"])
app.include_router(gameRouter, prefix="/api/game", tags=["Game"])


@app.get("/")
def root_route():
    return {"message": "Hello, World!"}
