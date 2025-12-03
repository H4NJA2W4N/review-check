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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["분석"])


# ===== 백그라운드 작업 헬퍼 =====

async def _process_analysis_background(analysis_id: int, review_url: str):
    """
    백그라운드에서 분석 처리
    
    🔥 중요: 새로운 DB 세션을 생성하여 사용
    """
    
    from models.database import SessionLocal
    
    # 백그라운드에서도 같은 로거 사용
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
    
    class Config:
        json_schema_extra = {
            "example": {
                "review_url": "https://www.musinsa.com/products/3242941"
            }
        }


class AnalysisResponse(BaseModel):
    """분석 응답"""
    success: bool = Field(..., description="성공 여부")
    result_code: int = Field(..., description="처리 결과 코드 (200: 성공, 600: 오류)")
    analysis_id: str = Field(..., description="생성된 분석 ID")
    status: str = Field(..., description="요청 상태 (queued)")
    message: str = Field(..., description="처리 결과 메시지")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "result_code": 200,
                "analysis_id": "123",
                "status": "queued",
                "message": "분석 요청이 접수되었습니다."
            }
        }


class AnalysisDetailResponse(BaseModel):
    """분석 상세 조회 응답"""
    success: bool
    analysis_id: int
    review_url: str
    status: str
    verdict: str | None = None
    confidence: float | None = None
    review_count: int | None = None
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


# ===== API 엔드포인트 =====

@router.post("/analyses", response_model=AnalysisResponse)
async def create_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    리뷰 분석 요청 생성 (유효성 검사 포함)
    
    - 무신사 상품 URL을 입력받아 리뷰 분석을 시작합니다
    - 백그라운드에서 크롤링 및 AI 분석을 수행합니다
    - 즉시 분석 ID와 상태를 반환합니다
    
    **처리 흐름:**
    1. URL 유효성 검사
    2. 분석 요청 생성 (status: queued)
    3. 백그라운드 작업 시작
        - 리뷰 크롤링
        - AI 서버로 분석 요청
        - 결과 저장 (status: completed)
    """
    
    try:
        # 1. URL 유효성 검사 (MusinsaCrawler에 위임)
        is_valid, error_msg, product_id = MusinsaCrawler.validate_url(request.review_url)
        if not is_valid:
            return AnalysisResponse(
                success=False,
                result_code=600,
                analysis_id="",
                status="",
                message=error_msg
            )
        
        # 2. 분석 요청 생성
        analysis = AnalysisService.create_analysis(db, request.review_url)
        
        logger.info(f"분석 요청 생성: ID={analysis.analysis_id}, URL={request.review_url}")
        
        # 3. 백그라운드 작업으로 분석 시작
        # 🔥 수정: db 세션 대신 새로운 세션을 생성하도록 함
        background_tasks.add_task(
            _process_analysis_background,
            analysis.analysis_id,
            request.review_url
        )
        
        # 4. 즉시 응답 반환
        return AnalysisResponse(
            success=True,
            result_code=200,
            analysis_id=str(analysis.analysis_id),
            status="queued",
            message="분석 요청이 접수되었습니다. 백그라운드에서 처리 중입니다."
        )
        
    except Exception as e:
        logger.error(f"분석 요청 생성 실패: {e}")
        return AnalysisResponse(
            success=False,
            result_code=600,
            analysis_id="",
            status="",
            message=f"분석 요청 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/analyses/{analysis_id}", response_model=AnalysisDetailResponse)
async def get_analysis_detail(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    분석 결과 조회
    
    - 분석 ID로 분석 결과를 조회합니다
    - 상태가 'completed'인 경우 최종 결과를 확인할 수 있습니다
    """
    try:
        analysis = AnalysisService.get_analysis(db, analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="분석 요청을 찾을 수 없습니다.")
        
        return AnalysisDetailResponse(
            success=True,
            analysis_id=analysis.analysis_id,
            review_url=analysis.review_url,
            status=analysis.status,
            verdict=analysis.verdict,
            confidence=float(analysis.confidence) if analysis.confidence else None,
            review_count=analysis.review_count,
            error_message=analysis.error_message,
            created_at=analysis.created_at.isoformat() if analysis.created_at else None,
            updated_at=analysis.updated_at.isoformat() if analysis.updated_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"분석 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/analyses")
async def list_analyses(
    skip: int = 0,
    limit: int = 10,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    분석 목록 조회
    
    - 최근 분석 요청 목록을 조회합니다
    - status로 필터링 가능 (queued, processing, completed, failed)
    """
    try:
        analyses = AnalysisService.list_analyses(
            db=db,
            status=status,
            skip=skip,
            limit=limit
        )
        
        return {
            'success': True,
            'count': len(analyses),
            'analyses': analyses
        }
        
    except Exception as e:
        logger.error(f"분석 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"분석 목록 조회 중 오류가 발생했습니다: {str(e)}")


# ===== 헬스 체크 =====

@router.get("/health")
async def health_check():
    """분석 서비스 헬스 체크"""
    return {
        "status": "healthy",
        "service": "analysis-service",
        "message": "분석 서비스가 정상 작동 중입니다."
    }