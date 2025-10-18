from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    PORT: int = 8000
    HOST: str = "0.0.0.0"

    APP_NAME: str = "Sudoku API"
    APP_VERSION: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    
    DB_URL: Union[str, None] = None

    ALLOWED_ORIGINS: Union[str, List[str]] = ["*"]

    PUZZLES_TO_GENERATE_PER_JOB: int = 5
    EASY_BLANKS: int = 40
    MEDIUM_BLANKS: int = 50
    HARD_BLANKS: int = 60

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SECRET_KEY: str = "secretkey"
    ALGORITHM: str = "HS256"

    



def get_settings() -> Settings:
    return Settings()


settings = get_settings()
