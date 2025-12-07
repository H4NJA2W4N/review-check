"""
사용자 피드백 모델 (재학습용 라벨 데이터)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class Feedback(Base):
    """사용자 피드백 (재학습용)"""
    __tablename__ = "feedbacks"
    
    feedback_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey('analyses.analysis_id'), nullable=False)
    review_text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)  # 해당 리뷰의 신뢰도 점수
    tags = Column(Integer, nullable=False)  # 1: 도움됨, 0: 부족함 (약한 라벨링)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    analysis = relationship("Analysis", back_populates="feedbacks")
    
    def to_dict(self):
        return {
            'feedback_id': self.feedback_id,
            'analysis_id': self.analysis_id,
            'review_text': self.review_text,
            'confidence': self.confidence,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }