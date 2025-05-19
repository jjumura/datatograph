# Project_A 백엔드

FastAPI를 사용한 백엔드 API 서버입니다.

## 설치 방법

1. 의존성 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
   - `.env.example` 파일을 복사하여 `.env` 파일 생성
   - 필요한 환경 변수 설정

## 실행 방법

개발 서버 실행:
```bash
uvicorn main:app --reload
```

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 