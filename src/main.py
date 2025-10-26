# src/main.py
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime

from src.Models import TableModels
from src.Config.settings import get_settings
from src.Config.database import init_database, create_db_and_tables, close_database, getSessionLocal
from src.API.Routes.auth_routes import router as authRouter
from src.API.Routes.user_routes import router as userRouter
from src.API.Routes.game_routers import router as gameRouter 
from src.API.Routes.challenges_routes import router as challengesRouter
from src.API.Routes.leaderboard_routes import router as leaderboardRouter
from src.Services.game_generator import generate_initial_games

try:
    from src.Config.scheduler import get_scheduler
    from src.Services.leaderboard_services import (
        update_all_time_high_leaderboard,
        update_periodic_leaderboard
    )
    scheduler = get_scheduler()
    SCHEDULER_ENABLED = True
    print("Scheduler and leaderboard services imported successfully.")
except ImportError:
    print("WARNING: Scheduler or leaderboard services not found. Background jobs will be disabled.")
    SCHEDULER_ENABLED = False

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Starting up application...")
    init_database()
    create_db_and_tables()

    if SCHEDULER_ENABLED: 
        print("Scheduler and leaderboard services enabled. Starting background jobs...")
        scheduler.add_job(
            update_periodic_leaderboard, 
            'cron', 
            hour=0, 
            minute=5, 
            args=['daily'], 
            id='update_daily_leaderboard', 
            replace_existing=True
        )
        scheduler.add_job(
        update_periodic_leaderboard, 
        'cron', 
        day_of_week='mon', 
        hour=1, 
        minute=5, 
        args=['weekly'], 
        id='update_weekly_leaderboard', 
        replace_existing=True
        )
        scheduler.add_job(
        update_all_time_high_leaderboard, 
        'interval', 
        hours=4, 
        id='update_all_time_leaderboard', 
        replace_existing=True
        )
        scheduler.start()

        tz = scheduler.timezone
        for job in scheduler.get_jobs():
            print(f"  - Triggering job: {job.id}")
            job.modify(next_run_time=datetime.now(tz))
    try:
        generate_initial_games()
    except Exception as e:
        print(f"Error generating initial games: {e}")
    yield
    # Shutdown
    print("Shutting down application...")
    if SCHEDULER_ENABLED and scheduler.running:
        scheduler.shutdown()
        print("Scheduler shut down.")
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
app.include_router(leaderboardRouter, prefix="/api/leaderboard", tags=["Leaderboard"])
app.include_router(challengesRouter, prefix="/api/challenges", tags=["Challenges"])


@app.get("/")
def root_route():
    return {"message": "Hello, World!"}
