"""
분석 API 라우터
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from models.database import get_db
from models.analysis import Analysis
from services.analysis_service import AnalysisService
from services.musinsa_api_crawler import MusinsaCrawler
import logging
from typing import List, Any, Optional, Dict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["분석"])


# ===== 백그라운드 작업 헬퍼 =====

async def _process_analysis_background(analysis_id: int, review_url: str):
    """
    백그라운드에서 분석 처리
    """
    from models.database import SessionLocal
    
    logger.info(f"========================================")
    logger.info(f"🚀 백그라운드 작업 시작: Analysis {analysis_id}")
    logger.info(f"========================================")
    
    db = SessionLocal()
    try:
        await AnalysisService.process_analysis(analysis_id, review_url, db)
        logger.info(f"✅ 백그라운드 작업 완료: Analysis {analysis_id}")
    except Exception as e:
        logger.error(f"❌ 백그라운드 분석 처리 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()
        logger.info(f"백그라운드 작업 종료: Analysis {analysis_id}")


# ===== Request/Response 모델 =====

class AnalysisRequest(BaseModel):
    """분석 요청"""
    review_url: str = Field(..., description="분석 대상 리뷰 URL")

class AnalysisResponse(BaseModel):
    """분석 응답"""
    success: bool
    result_code: int
    analysis_id: str
    status: str
    message: str

# 🚨 [범인 검거] 여기가 문제였습니다! 필드를 추가해줘야 프론트엔드로 나갑니다.
class AnalysisDetailResponse(BaseModel):
    """분석 상세 조회 응답"""
    success: bool
    analysis_id: int
    review_url: str
    status: str
    verdict: str | None = None
    confidence: float | None = None
    score: int | None = None           # ✅ 프론트엔드 원형 그래프용 점수
    review_count: int | None = None
    error_message: str | None = None
    avg_rating: float | None = None
    
    # ✅ [핵심 수정] 리스트 데이터가 통과할 수 있도록 문을 열어줍니다.
    top_reviews: List[Any] | None = []
    worst_reviews: List[Any] | None = []
    summary: str | None = None          
    
    created_at: str | None = None
    updated_at: str | None = None


# ===== API 엔드포인트 =====

@router.post("/analyses", response_model=AnalysisResponse)
async def create_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """리뷰 분석 요청 생성"""
    try:
        # 1. URL 유효성 검사
        is_valid, error_msg, product_id = MusinsaCrawler.validate_url(request.review_url)
        if not is_valid:
            return AnalysisResponse(
                success=False, result_code=600, analysis_id="", status="", message=error_msg
            )
        
        # 2. 분석 요청 생성
        analysis = AnalysisService.create_analysis(db, request.review_url)
        logger.info(f"분석 요청 생성: ID={analysis.analysis_id}")
        
        # 3. 백그라운드 작업
        background_tasks.add_task(
            _process_analysis_background, analysis.analysis_id, request.review_url
        )
        
        return AnalysisResponse(
            success=True, result_code=200, 
            analysis_id=str(analysis.analysis_id), status="queued",
            message="분석 요청이 접수되었습니다."
        )
        
    except Exception as e:
        logger.error(f"분석 요청 생성 실패: {e}")
        return AnalysisResponse(
            success=False, result_code=600, analysis_id="", status="", message=str(e)
        )


@router.get("/analyses/{analysis_id}", response_model=AnalysisDetailResponse)
async def get_analysis_detail(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """분석 결과 조회"""
    try:
        analysis = AnalysisService.get_analysis(db, analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="분석 요청을 찾을 수 없습니다.")
        
        # ✅ [중요] DB 데이터를 안전한 리스트로 변환 (to_dict 사용)
        data = analysis.to_dict()
        
        return AnalysisDetailResponse(
            success=True,
            analysis_id=data['analysis_id'],
            review_url=data['review_url'],
            status=data['status'],
            verdict=data['verdict'],
            confidence=data['confidence'],
            score=int(data['confidence']) if data['confidence'] else 0,
            review_count=data['review_count'],
            error_message=data['error_message'],
            avg_rating=data.get('avg_rating', 0),
            
            # ✅ 변환된 데이터를 여기에 담아 보냅니다.
            top_reviews=data.get('top_reviews', []),
            worst_reviews=data.get('worst_reviews', []),
            summary=data.get('summary', ''),
            
            created_at=data['created_at'],
            updated_at=data['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyses")
async def list_analyses(
    skip: int = 0, limit: int = 10, status: str = None, db: Session = Depends(get_db)
):
    """분석 목록 조회"""
    try:
        analyses = AnalysisService.list_analyses(db, status, skip, limit)
        return {'success': True, 'count': len(analyses), 'analyses': analyses}
    except Exception as e:
        logger.error(f"목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))