# Project_A

## 환경 설정

### 필수 요구 사항
- Python 3.9 이상
- Node.js 16 이상
- npm 7 이상

### 백엔드 설정
1. 백엔드 디렉토리로 이동:
   ```
   cd backend
   ```

2. 가상 환경 생성 및 활성화:
   ```
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. 의존성 설치:
   ```
   pip install -r requirements.txt
   ```

4. 환경 변수 설정:
   ```
   cp .env.example .env
   # .env 파일을 열고 실제 값으로 수정하세요
   ```

5. 서버 실행:
   ```
   python -m uvicorn main:app --reload
   ```

### 프론트엔드 설정
1. 프론트엔드 디렉토리로 이동:
   ```
   cd frontend
   ```

2. 의존성 설치:
   ```
   npm install
   ```

3. 개발 서버 실행:
   ```
   npm run dev
   ```

## 자동 설정 스크립트 사용
Windows에서는 `setup.bat`를, Linux/Mac에서는 `setup.sh`를 실행하여 자동으로 프로젝트를 설정할 수 있습니다.
