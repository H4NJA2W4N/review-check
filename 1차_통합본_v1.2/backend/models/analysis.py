# backend/models/analysis.py
from sqlalchemy import Column, Integer, Numeric, String, Float, DateTime, Text, func, JSON  # ✅ JSON 추가됨
from sqlalchemy.orm import relationship
from models.database import Base
import json

class Analysis(Base):
    __tablename__ = "analyses"

    # 기본 정보
    analysis_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    review_url = Column(String(500), nullable=False, index=True)
    
    # 분석 상태
    status = Column(String(50), nullable=False, default='queued', index=True)
    
    # 분석 결과
    verdict = Column(String(50), nullable=True)
    confidence = Column(Numeric(5, 2), nullable=True)
    
    # 리뷰 샘플 저장용 (리스트를 통째로 저장)
    top_reviews = Column(JSON, nullable=True)
    worst_reviews = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)

    # 추가 정보
    error_message = Column(String(500), nullable=True)
    review_count = Column(Integer, nullable=True)
    avg_rating = Column(Float, nullable=True)
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationship
    feedbacks = relationship("Feedback", back_populates="analysis", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Analysis(id={self.analysis_id}, url={self.review_url[:50]}, status={self.status})>"
    
    def to_dict(self):
        """딕셔너리로 변환"""
        # 1. top_reviews 안전하게 가져오기
        top = self.top_reviews
        if isinstance(top, str): # 만약 문자열로 되어있다면
            try:
                top = json.loads(top) # 리스트로 변환
            except:
                top = [] # 에러나면 빈 리스트
        elif top is None:
            top = []

        # 2. worst_reviews 안전하게 가져오기
        worst = self.worst_reviews
        if isinstance(worst, str): # 만약 문자열로 되어있다면
            try:
                worst = json.loads(worst) # 리스트로 변환
            except:
                worst = []
        elif worst is None:
            worst = []

        return {
            'analysis_id': self.analysis_id,
            'review_url': self.review_url,
            'status': self.status,
            'verdict': self.verdict,
            'confidence': float(self.confidence) if self.confidence else None,
            'error_message': self.error_message,
            'review_count': self.review_count,
            
            #프론트엔드로 보낼 때 포함
            'top_reviews': self.top_reviews,
            'worst_reviews': self.worst_reviews,
            'summary': self.summary,
            'avg_rating': self.avg_rating,

            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }