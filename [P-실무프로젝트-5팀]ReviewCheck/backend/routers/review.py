from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import random

# 데이터베이스 및 모델 연결
from models.database import get_db
from models.analysis import Analysis  # 아까 만든 모델 파일

router = APIRouter()

# 요청 받을 데이터 형식 정의
class AnalyzeRequest(BaseModel):
    url: str

@router.post("/analyze")
def analyze_review(request: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    [테스트용] 리뷰 분석 요청 API
    - URL을 입력받아 가짜 분석 결과를 DB에 저장합니다.
    """
    
    # 1. 랜덤한 신뢰도 점수 생성 (50점 ~ 100점 사이)
    fake_score = round(random.uniform(50.0, 99.9), 1)

    # 2. DB에 저장할 데이터 객체 만들기
    new_analysis = Analysis(
        url=request.url,
        reliability=fake_score,
        created_at=datetime.now()
    )

    # 3. DB에 저장
    db.add(new_analysis)
    db.commit()
    db.refresh(new_analysis)

    return {
        "success": True,
        "message": "분석 데이터 생성 완료",
        "data": {
            "id": new_analysis.analysis_id,
            "url": new_analysis.url,
            "score": new_analysis.reliability,
            "created_at": new_analysis.created_at
        }
    }