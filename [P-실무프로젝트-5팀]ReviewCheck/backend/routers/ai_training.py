"""
AI 모델 재학습 관리 API
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models.database import get_db
from models.ai_job import AIJob
from models.ai_model import AIModel
from models.admin import Admin
from models.feedback import Feedback
from utils.dependencies import get_current_admin
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/ai", tags=["AI 재학습"])


class RetrainRequest(BaseModel):
    """재학습 요청"""
    description: str = ""


class RetrainResponse(BaseModel):
    """재학습 응답"""
    success: bool
    message: str
    job_id: int = None


@router.post("/retrain", response_model=RetrainResponse)
async def request_retrain(
    request: RetrainRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    AI 모델 재학습 요청
    
    - feedbacks 테이블의 데이터를 사용하여 KcELECTRA 모델 재학습
    - ai_jobs 테이블에 작업 추가
    - 백그라운드 train_model.py가 주기적으로 체크하여 실행
    """
    try:
        logger.info(f"🤖 AI 재학습 요청: 관리자={current_admin.username}")
        
        # 1. 피드백 데이터 확인
        feedback_count = db.query(Feedback).count()
        
        if feedback_count == 0:
            return RetrainResponse(
                success=False,
                message="재학습에 사용할 피드백 데이터가 없습니다. 사용자 피드백을 먼저 수집해주세요."
            )
        
        logger.info(f"📊 사용 가능한 피드백: {feedback_count}개")
        
        # 2. 현재 활성 모델 조회
        active_model = db.query(AIModel).filter(AIModel.active == True).first()
        
        if not active_model:
            # 초기 모델이 없으면 생성
            logger.warning("⚠️ 활성 모델 없음. 초기 모델 생성 중...")
            active_model = AIModel(
                model_name="KcELECTRA-review-analyzer",
                version="v1.0",
                artifact_url="ai_models",
                description="초기 모델",
                active=True
            )
            db.add(active_model)
            db.commit()
            db.refresh(active_model)
        
        # 3. ai_jobs에 재학습 작업 추가
        job = AIJob(
            model_id=active_model.model_id,
            submitted_by=current_admin.admin_id,
            type='training',
            status='pending',
            logs=f"재학습 요청: {request.description}\n피드백 데이터: {feedback_count}개"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"✅ 재학습 작업 생성: job_id={job.job_id}")
        
        return RetrainResponse(
            success=True,
            message=f"새로운 학습 요청이 접수되었습니다. (작업 ID: {job.job_id}, 피드백: {feedback_count}개)",
            job_id=job.job_id
        )
        
    except Exception as e:
        logger.error(f"❌ 재학습 요청 실패: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"재학습 요청 중 오류: {str(e)}")


@router.get("/jobs")
async def list_jobs(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """AI 작업 목록 조회"""
    try:
        jobs = db.query(AIJob).order_by(AIJob.submitted_at.desc()).limit(20).all()
        return {
            'success': True,
            'jobs': [job.to_dict() for job in jobs]
        }
    except Exception as e:
        logger.error(f"작업 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """AI 작업 상태 조회"""
    try:
        job = db.query(AIJob).filter(AIJob.job_id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
        return {
            'success': True,
            'job': job.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"작업 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """AI 모델 목록 조회"""
    try:
        models = db.query(AIModel).order_by(AIModel.created_at.desc()).all()
        return {
            'success': True,
            'models': [model.to_dict() for model in models]
        }
    except Exception as e:
        logger.error(f"모델 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_training_stats(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """재학습 통계"""
    try:
        total_jobs = db.query(AIJob).filter(AIJob.type == 'training').count()
        pending_jobs = db.query(AIJob).filter(
            AIJob.type == 'training',
            AIJob.status == 'pending'
        ).count()
        completed_jobs = db.query(AIJob).filter(
            AIJob.type == 'training',
            AIJob.status == 'completed'
        ).count()
        
        total_feedbacks = db.query(Feedback).count()
        active_model = db.query(AIModel).filter(AIModel.active == True).first()
        
        return {
            'success': True,
            'total_jobs': total_jobs,
            'pending_jobs': pending_jobs,
            'completed_jobs': completed_jobs,
            'total_feedbacks': total_feedbacks,
            'active_model': active_model.to_dict() if active_model else None
        }
    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))