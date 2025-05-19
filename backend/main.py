from dotenv import load_dotenv
import os
import logging
import logging.config
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pathlib import Path

load_dotenv()  # .env 파일을 로드합니다

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# from app.utils.visualize import process_excel_for_visualization # 이제 visualize_router에서 처리
from app.utils.visualize import cleanup_old_charts # shutdown_event에서 사용
from app.routes.api import router as api_router
from app.routes.excel import router as excel_router
from app.routes.visualize import router as visualize_router
from app.routes.ai import router as ai_router

# 로깅 기본 설정
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "fastapi": {"handlers": ["console"], "level": "INFO", "propagate": False},
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Project_A API",
    description="FastAPI 기반 백엔드 API",
    version="0.1.0"
)

# 글로벌 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        logger.error(f"HTTPException for request {request.method} {request.url}: Status Code {exc.status_code}, Detail: {exc.detail}", exc_info=False) # HTTPException의 detail은 이미 충분한 정보일 수 있음
        raise exc # FastAPI의 기본 핸들러가 처리하도록 다시 발생
    
    logger.exception(f"Unhandled exception for request {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error_type": exc.__class__.__name__},
    )

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000"), # .env 파일에서 FRONTEND_URL 설정 가능
        "http://localhost:3000", # 기본 프론트엔드 포트
        "http://localhost:3001", # Vite가 사용하는 대체 포트
        # 필요한 경우 여기에 프로덕션 프론트엔드 URL 추가
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# main.py에서 직접 정의했던 /visualize/excel 관련 함수 및 변수는 삭제되었습니다.
# (ALLOWED_MIME_TYPES, ALLOWED_EXTENSIONS, validate_file, visualize_excel 함수)
# 이들은 각 라우터 또는 유틸리티 모듈에서 필요에 따라 관리됩니다.

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup...")
    Path("temp_charts").mkdir(exist_ok=True)
    logger.info("temp_charts directory ensured.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown...")
    cleanup_old_charts(max_age_hours=0)
    logger.info("Temporary charts cleaned up.")

@app.get("/")
async def root():
    return {"message": "Project_A FastAPI 백엔드에 오신 것을 환영합니다"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 라우터 등록 (올바른 prefix 사용)
app.include_router(api_router, prefix="/api")
app.include_router(excel_router, prefix="/api/excel")
app.include_router(visualize_router, prefix="/api/visualize") # 프론트엔드 호출 경로와 일치
app.include_router(ai_router, prefix="/api/ai")

if __name__ == "__main__":
    import uvicorn
    # Uvicorn 실행 시 애플리케이션 레벨 로깅 설정을 사용하도록 log_config=None 전달
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_config=None)