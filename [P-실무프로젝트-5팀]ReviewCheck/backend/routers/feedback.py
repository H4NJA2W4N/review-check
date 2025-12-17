"""
사용자 피드백 API
Smart Labeling (Hybrid 방식) 적용
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models.database import get_db
from models.analysis import Analysis
from models.feedback import Feedback
from typing import Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["피드백"])


class FeedbackRequest(BaseModel):
    """피드백 요청"""
    analysis_id: int
    is_helpful: bool  # True: 도움됨(👍), False: 부족함(👎)
    strategy: str = "hybrid"  # Smart Labeling 전략: "weak", "hybrid", "extreme", "relative"


class FeedbackResponse(BaseModel):
    """피드백 응답"""
    success: bool
    message: str
    feedback_count: int = 0
    strategy_info: Optional[dict] = None


# ============================================================================
# Smart Labeling 전략 함수들
# ============================================================================

def smart_label_hybrid(
    score: float, 
    avg_score: float, 
    user_satisfaction: int
) -> Optional[int]:
    """
    🎯 Hybrid Smart Labeling (추천)
    
    극단값은 확정, 중간값은 상대적 라벨링
    
    Args:
        score: 모델 예측 점수 (0-100)
        avg_score: 분석 내 평균 점수
        user_satisfaction: 사용자 만족도 (0 or 1)
    
    Returns:
        label (0 or 1) or None (학습 데이터에서 제외)
    """
    if user_satisfaction == 1:  # 👍 (전체적으로 만족)
        # 극단적으로 높음 → 확실히 좋은 리뷰
        if score >= 85:
            return 1
        # 극단적으로 낮음 → 실제로는 나쁜 리뷰
        elif score <= 35:
            return 0
        # 중간값 → 상대적 라벨링
        else:
            # 평균보다 높으면 좋음, 낮으면 나쁨
            return 1 if score > avg_score else 0
    
    else:  # 👎 (전체적으로 불만족)
        # 극단적으로 낮음 → 확실히 나쁜 리뷰
        if score <= 35:
            return 0
        # 극단적으로 높음 → 실제로는 좋은 리뷰
        elif score >= 85:
            return 1
        # 중간값 → 상대적 라벨링
        else:
            # 평균보다 낮으면 나쁨, 높으면 좋음
            return 0 if score < avg_score else 1


def smart_label_extreme(
    score: float, 
    user_satisfaction: int
) -> Optional[int]:
    """
    극단값만 사용 (Confident Samples Only)
    
    확실한 케이스만 학습 데이터로 사용
    """
    if user_satisfaction == 1:  # 👍
        if score >= 80:
            return 1  # 높은 점수 → 확실히 좋음
        elif score <= 40:
            return 0  # 낮은 점수 → 사실은 나쁨
        else:
            return None  # 애매함 → 제외
    else:  # 👎
        if score <= 40:
            return 0  # 낮은 점수 → 확실히 나쁨
        elif score >= 80:
            return 1  # 높은 점수 → 사실은 좋음
        else:
            return None  # 애매함 → 제외


def smart_label_relative(
    score: float, 
    avg_score: float, 
    user_satisfaction: int
) -> int:
    """
    상대적 라벨링
    
    분석 내에서 상대적으로 좋은/나쁜 리뷰 구분
    """
    if user_satisfaction == 1:  # 👍
        # 평균보다 높으면 label=1, 낮으면 label=0
        return 1 if score > avg_score else 0
    else:  # 👎
        # 평균보다 낮으면 label=0, 높으면 label=1
        return 0 if score < avg_score else 1


def calculate_label_confidence(score: float, label: int) -> float:
    """
    라벨 신뢰도 계산
    
    점수와 라벨이 일치할수록 신뢰도 높음
    
    Args:
        score: 모델 예측 점수 (0-100)
        label: 부여된 라벨 (0 or 1)
    
    Returns:
        신뢰도 (0.0-1.0)
    """
    if label == 1:
        # label=1인데 점수가 높을수록 신뢰도 높음
        return min(score / 100.0, 1.0)
    else:
        # label=0인데 점수가 낮을수록 신뢰도 높음
        return min((100 - score) / 100.0, 1.0)
    

# ============================================================================
# API 엔드포인트
# ============================================================================

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    전체 분석 결과에 대한 피드백 제출 (Smart Labeling)
    
    Smart Labeling 전략:
    - weak: 기존 방식 (모든 리뷰에 동일 라벨)
    - hybrid: 극단값 + 상대적 라벨링 (현재 방식)
    - extreme: 극단값만 사용
    - relative: 상대적 라벨링만 사용
    """
    try:
        logger.info(f"📝 피드백 요청: analysis_id={request.analysis_id}, helpful={request.is_helpful}, strategy={request.strategy}")
        
        # 1. 분석 데이터 조회
        analysis = db.query(Analysis).filter(
            Analysis.analysis_id == request.analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
        
        if analysis.status != 'completed':
            raise HTTPException(status_code=400, detail="완료되지 않은 분석입니다.")
        
        # 2. 모든 리뷰 수집
        all_reviews = []
        
        # top_reviews와 worst_reviews 모두 수집
        if analysis.top_reviews:
            all_reviews.extend(analysis.top_reviews)
        if analysis.worst_reviews:
            all_reviews.extend(analysis.worst_reviews)
        
        if not all_reviews:
            raise HTTPException(status_code=400, detail="리뷰 데이터가 없습니다.")
        
        # 3. 점수 추출 및 평균 계산
        scores = []
        for review in all_reviews:
            score = review.get('reliability_score', 0)
            scores.append(score)
        
        avg_score = np.mean(scores) if scores else 50.0
        
        logger.info(f"📊 리뷰 통계: 총 {len(all_reviews)}개, 평균 점수 {avg_score:.1f}")
        
        # 4. 사용자 만족도 (0 or 1)
        user_satisfaction = 1 if request.is_helpful else 0

        # 5. 기존 피드백 삭제 (중복 방지)
        db.query(Feedback).filter(
            Feedback.analysis_id == request.analysis_id
        ).delete()
        
        # 6. Smart Labeling 적용하여 저장
        saved_count = 0
        skipped_count = 0
        label_stats = {'label_0': 0, 'label_1': 0}
        
        for review in all_reviews:
            review_text = review.get('content', '') or review.get('text', '')
            score = review.get('reliability_score', 0)
            
            if not review_text:
                continue
            
            # ⭐ Smart Labeling 전략 적용
            label = None
            
            if request.strategy == "weak":
                # 기존 방식: 모든 리뷰에 동일 라벨
                label = user_satisfaction
            
            elif request.strategy == "hybrid":
                # Hybrid: 극단값 + 상대적 라벨링 (추천)
                label = smart_label_hybrid(score, avg_score, user_satisfaction)
            
            elif request.strategy == "extreme":
                # Extreme: 극단값만 사용
                label = smart_label_extreme(score, user_satisfaction)
            
            elif request.strategy == "relative":
                # Relative: 상대적 라벨링만
                label = smart_label_relative(score, avg_score, user_satisfaction)
            
            else:
                # 기본값: hybrid
                label = smart_label_hybrid(score, avg_score, user_satisfaction)
            
            # label이 None이면 스킵 (학습 데이터에서 제외)
            if label is None:
                skipped_count += 1
                logger.debug(f"⏭️ 스킵: score={score:.1f} (애매한 케이스)")
                continue
            
            # 라벨 신뢰도 계산
            label_conf = calculate_label_confidence(score, label)
            
            # 피드백 저장
            feedback = Feedback(
                analysis_id=request.analysis_id,
                review_text=review_text,
                confidence=score,
                tags=label,
                original_score=score,
                labeling_strategy=request.strategy,
                label_confidence=label_conf
            )
            db.add(feedback)
            
            saved_count += 1
            label_stats[f'label_{label}'] += 1
            
            logger.debug(f"✅ 저장: score={score:.1f} → label={label}, "
                        f"confidence={label_conf:.2f}")
        
        db.commit()
        
        logger.info(f"✅ 피드백 저장 완료: {saved_count}개 리뷰 (라벨={label})")
        
        # 7. 결과 로깅
        logger.info(f"🎯 Smart Labeling 완료:")
        logger.info(f"   - 전략: {request.strategy}")
        logger.info(f"   - 저장: {saved_count}개")
        logger.info(f"   - 제외: {skipped_count}개")
        logger.info(f"   - label=1: {label_stats['label_1']}개")
        logger.info(f"   - label=0: {label_stats['label_0']}개")
        logger.info(f"   - 평균 점수: {avg_score:.1f}")
        
        # 8. 응답 생성
        strategy_info = {
            'strategy': request.strategy,
            'total_reviews': len(all_reviews),
            'saved': saved_count,
            'skipped': skipped_count,
            'label_distribution': label_stats,
            'average_score': float(avg_score)
        }

        return FeedbackResponse(
            success=True,
            message=f"피드백이 저장되었습니다. 감사합니다! "
                   f"(저장: {saved_count}개, 제외: {skipped_count}개)",
            feedback_count=saved_count,
            strategy_info=strategy_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 피드백 저장 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
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