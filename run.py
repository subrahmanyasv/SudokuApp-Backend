from src.Config.settings import get_settings
from src.main import app
import uvicorn
import sys


def create_app(): 
    try:
        settings = get_settings()
        uvicorn.run(
            app,
            host= settings.HOST,
            port= settings.PORT,
            reload= settings.debug
        )
    except Exception as e:
        print(f"Error starting the server: {e}")   
        sys.exit(1)



if __name__ == "__main__":
    create_app()

