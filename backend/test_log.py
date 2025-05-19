import logging
import logging.config
from fastapi import FastAPI

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(levelname)s - %(module)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG", # 로그 레벨을 DEBUG로 낮춰 더 많은 로그 확인
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logger.info("Test application startup...")
    logger.debug("This is a DEBUG message from startup.")

@app.get("/")
async def read_root():
    logger.info("Root endpoint called.")
    return {"Hello": "World"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn for test_log.py...")
    uvicorn.run("test_log:app", host="0.0.0.0", port=8001, reload=True, log_config=None) 