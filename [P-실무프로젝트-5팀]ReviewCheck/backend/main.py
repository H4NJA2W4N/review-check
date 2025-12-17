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
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()  # .env 파일 로드
import os

print(f"[STARTUP] GEMINI_API_KEY 로드 확인: {'설정됨' if os.getenv('GEMINI_API_KEY') else '없음'}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime

from models.database import SessionLocal, engine, Base
from models.admin import Admin
from models.ai_model import AIModel
from services.admin_service import create_admin
from models.database import get_db
from config import ALLOWED_ORIGINS

# 라우터 임포트
from routers import admin
from routers import notice
from routers import inquiry
from routers import crawling
from routers import analysis
from routers import feedback, ai_training

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

origins = [
    "http://localhost:5173",    # 프론트엔드 주소 (가끔 127.0.0.1로 뜰 때도 있으니 둘 다 넣으세요)
    "http://127.0.0.1:5173",
]

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
app.include_router(feedback.router, tags=["피드백"])
app.include_router(ai_training.router, tags=["AI 모델 학습"]) 

current_ai_model = None

@app.on_event("startup")
async def startup_event():
    """
    서버 시작 시 기본 관리자 계정 생성 및 활성 AI 모델 로딩
    """
    global current_ai_model
    
    logger.info("="*60)
    logger.info("🚀 서버 시작: 기본 관리자 계정 생성 및 AI 모델 로딩")
    logger.info("="*60)
    
    db = SessionLocal()
    try:
        # 1. 기본 관리자 계정 생성
        existing_admin = db.query(Admin).filter(Admin.username == "admin").first()
        if not existing_admin:
            create_admin(db, username="admin", password="admin123")
            logger.info("✅ 기본 관리자 계정 생성됨: admin / admin123")
        else:
            logger.info("ℹ️  기본 관리자 계정이 이미 존재합니다.")

        # 2. active=True인 최신 모델 조회
        active_model = db.query(AIModel).filter(
            AIModel.active == True
        ).order_by(AIModel.created_at.desc()).first()
        
        if active_model:
            current_ai_model = active_model
            logger.info(f"✅ 활성 모델 로딩: {active_model.model_name} {active_model.version}")
            logger.info(f"   경로: {active_model.artifact_url}")
            #logger.info(f"   정확도: {active_model.accuracy}")
        else:
            # 초기 모델 생성
            logger.warning("⚠️ 활성 모델 없음. 초기 모델 등록 중...")
            initial_model = AIModel(
                model_name="RandomForest-review-scorer",
                version="v1.0",
                artifact_url="ai_models",  # 기존 RF 모델 경로 (final_perfect_scorer.pkl)
                description="초기 Random Forest 모델 (KcELECTRA + RF 조합)",
                active=True
            )
            db.add(initial_model)
            db.commit()
            db.refresh(initial_model)
            
            current_ai_model = initial_model
            logger.info(f"✅ 초기 모델 등록 완료: {initial_model.version}")
            
    except Exception as e:
        logger.error(f"❌ 모델 로딩 실패: {e}")
    finally:
        db.close()
    
    logger.info("="*60)


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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 개발 중에는 True, 프로덕션에서는 False
    )