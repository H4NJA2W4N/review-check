"""
사용자 피드백 API
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models.database import get_db
from models.analysis import Analysis
from models.feedback import Feedback
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["피드백"])


class FeedbackRequest(BaseModel):
    """피드백 요청"""
    analysis_id: int
    is_helpful: bool  # True: 도움됨(👍), False: 부족함(👎)


class FeedbackResponse(BaseModel):
    """피드백 응답"""
    success: bool
    message: str
    feedback_count: int = 0


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    전체 분석 결과에 대한 피드백 제출
    
    약한 라벨링(Weak Labeling):
    - 👍 (도움됨) = 모델 판단에 동의 → 모든 리뷰에 label 1
    - 👎 (부족함) = 모델 판단에 불만 → 모든 리뷰에 label 0
    """
    try:
        logger.info(f"📝 피드백 요청: analysis_id={request.analysis_id}, helpful={request.is_helpful}")
        
        # 1. 분석 데이터 조회
        analysis = db.query(Analysis).filter(
            Analysis.analysis_id == request.analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
        
        if analysis.status != 'completed':
            raise HTTPException(status_code=400, detail="완료되지 않은 분석입니다.")
        
        # 2. 약한 라벨링 (Weak Labeling)
        # 👍 = 1 (모델 판단 동의), 👎 = 0 (모델 판단 불만)
        label = 1 if request.is_helpful else 0
        
        logger.info(f"🏷️ 라벨: {label} ({'도움됨' if label == 1 else '부족함'})")
        
        # 3. 모든 리뷰에 동일한 라벨 부여
        all_reviews = []
        
        # top_reviews와 worst_reviews 모두 수집
        if analysis.top_reviews:
            all_reviews.extend(analysis.top_reviews)
        if analysis.worst_reviews:
            all_reviews.extend(analysis.worst_reviews)
        
        if not all_reviews:
            raise HTTPException(status_code=400, detail="리뷰 데이터가 없습니다.")
        
        # 4. 기존 피드백 삭제 (중복 방지)
        db.query(Feedback).filter(
            Feedback.analysis_id == request.analysis_id
        ).delete()
        
        # 5. feedbacks 테이블에 저장
        feedback_count = 0
        for review in all_reviews:
            review_text = review.get('content', '') or review.get('text', '')
            confidence = review.get('reliability_score', 0)
            
            if not review_text:
                continue
            
            feedback = Feedback(
                analysis_id=request.analysis_id,
                review_text=review_text,
                confidence=confidence,
                tags=label  # 모든 리뷰에 동일한 라벨
            )
            db.add(feedback)
            feedback_count += 1
        
        db.commit()
        
        logger.info(f"✅ 피드백 저장 완료: {feedback_count}개 리뷰 (라벨={label})")
        
        return FeedbackResponse(
            success=True,
            message=f"피드백이 저장되었습니다. 감사합니다! (저장된 리뷰: {feedback_count}개)",
            feedback_count=feedback_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 피드백 저장 실패: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"피드백 저장 중 오류: {str(e)}")


@router.get("/feedback/stats")
async def get_feedback_stats(db: Session = Depends(get_db)):
    """
    피드백 통계 조회
    """
    try:
        total = db.query(Feedback).count()
        helpful = db.query(Feedback).filter(Feedback.tags == 1).count()
        unhelpful = db.query(Feedback).filter(Feedback.tags == 0).count()
        
        return {
            'success': True,
            'total': total,
            'helpful': helpful,
            'unhelpful': unhelpful
        }
    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))