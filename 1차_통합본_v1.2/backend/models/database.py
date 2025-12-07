#
# MariaDB 데이터베이스 연결 설정 파일
#

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL, USE_SQLITE

# 데이터베이스 엔진 생성
if USE_SQLITE:
    # SQLite 설정
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # FastAPI에서 필요
        echo=False  # SQL 쿼리 로깅 끄기 (필요시 True로 변경)
    )
else:
    # MariaDB/MySQL 설정
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=5,
        max_overflow=10,
        echo=False  # SQL 쿼리 로깅 (개발 시)
    )
print("🔍 USING DATABASE:", DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()