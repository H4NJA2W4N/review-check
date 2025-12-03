"""
분석 요청 모델 (Analysis)
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric
from sqlalchemy.sql import func
from models.database import Base


class Analysis(Base):
    """분석 요청 테이블"""
    __tablename__ = "analyses"
    
    # 기본 정보
    analysis_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    review_url = Column(String(500), nullable=False, index=True)  # 무신사 상품 URL
    
    # 분석 상태
    status = Column(String(50), nullable=False, default='queued', index=True)
    # 상태 값: 'queued', 'processing', 'completed', 'failed'
    
    # 분석 결과
    verdict = Column(String(50), nullable=True)
    # 결과 값: 'safe', 'suspicious', 'malicious', None
    
    confidence = Column(Numeric(5, 2), nullable=True)
    # 신뢰도: 0.00 ~ 100.00 (퍼센트)
    
    # 추가 정보 (선택적)
    error_message = Column(String(500), nullable=True)  # 에러 발생 시 메시지
    review_count = Column(Integer, nullable=True)  # 분석된 리뷰 개수
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Analysis(id={self.analysis_id}, url={self.review_url[:50]}, status={self.status})>"
    
    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            'analysis_id': self.analysis_id,
            'review_url': self.review_url,
            'status': self.status,
            'verdict': self.verdict,
            'confidence': float(self.confidence) if self.confidence else None,
            'error_message': self.error_message,
            'review_count': self.review_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }