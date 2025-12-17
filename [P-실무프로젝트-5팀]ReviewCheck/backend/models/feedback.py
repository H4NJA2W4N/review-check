"""
사용자 피드백 모델 (재학습용 라벨 데이터)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class Feedback(Base):
    """사용자 피드백 (재학습용) - Smart Labeling"""
    __tablename__ = "feedbacks"
    
    feedback_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey('analyses.analysis_id'), nullable=False)
    review_text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)  # 해당 리뷰의 신뢰도 점수
    tags = Column(Integer, nullable=False)  # 1: 도움됨, 0: 부족함 (스마트 라벨링)

    # ⭐ Smart Labeling 관련 컬럼
    original_score = Column(Float, nullable=True)  # 모델 원본 점수 (0-100)
    labeling_strategy = Column(String(50), nullable=True, default='hybrid')  # 라벨링 전략
    label_confidence = Column(Float, nullable=True)  # 라벨 신뢰도 (0.0-1.0)

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
            'original_score': self.original_score,
            'labeling_strategy': self.labeling_strategy,
            'label_confidence': self.label_confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }