from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from src.Config.settings import get_settings

settings = get_settings()

scheduler = AsyncIOScheduler(timezone = "UTC")

def get_scheduler():
    return scheduler