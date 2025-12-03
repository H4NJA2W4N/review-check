"""
Review Check - 모놀리식 애플리케이션
쇼핑몰 리뷰 신뢰도 분석 시스템
"""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime

from models.database import engine, Base
from models.admin import Admin
from services.admin_service import create_admin
from models.database import get_db
from config import ALLOWED_ORIGINS

# 라우터 임포트
from routers import admin
from routers import notice
from routers import inquiry
from routers import crawling
from routers import analysis

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Review Check API",
    description="쇼핑몰 리뷰 신뢰도 분석 시스템",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (선택사항)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# 라우터 등록
app.include_router(admin.router, prefix="/admin", tags=["관리자"])
app.include_router(notice.router, tags=["공지사항"])
app.include_router(inquiry.router, tags=["문의"])
app.include_router(crawling.router, tags=["리뷰 크롤링"])
app.include_router(analysis.router, tags=["분석"])

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    print("=" * 60)
    print("🚀 Review Check API 서버 시작")
    print("=" * 60)
    
    # 기본 관리자 계정 생성
    db = next(get_db())
    try:
        existing = db.query(Admin).filter(Admin.username == "admin").first()
        if not existing:
            create_admin(db, username="admin", password="admin123")
            print("✅ 기본 관리자 계정 생성됨: admin / admin123")
        else:
            print("ℹ️  기본 관리자 계정이 이미 존재합니다.")
    except Exception as e:
        print(f"❌ 관리자 계정 생성 오류: {e}")
    finally:
        db.close()
    
    print("=" * 60)


@app.get("/")
def root():
    """루트 엔드포인트"""
    return {
        "service": "Review Check API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "review-check-api",
        "timestamp": datetime.utcnow().isoformat()
    }