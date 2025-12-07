import os
from datetime import timedelta

# backend/config.py의 절대경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/
# backend/app.db 로 고정
DB_PATH = os.path.join(BASE_DIR, "app.db")  # backend/app.db

# 데이터베이스 설정
# 개발/테스트: SQLite 사용 (별도 설치 불필요)
# 프로덕션: MariaDB 사용
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"


if USE_SQLITE:
    # SQLite - 파일 기반 데이터베이스 (admin.db 파일에 저장)
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
else:
    # MariaDB - 학과 서버 연결 시 사용
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://admin:admin123@localhost:3306/app_db"
    )

# JWT 설정
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24  # 24시간

# CORS 설정
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "*"  # 개발 중에는 모든 origin 허용
]