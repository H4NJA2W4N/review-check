"""
AI 모델 버전 관리 테이블
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class AIModel(Base):
    """AI 모델 버전 관리"""
    __tablename__ = "ai_models"
    
    model_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_name = Column(String(100), nullable=False)  # 예: "KcELECTRA-review-analyzer"
    version = Column(String(50), nullable=False)  # 예: "v1.0", "v1.1"
    artifact_url = Column(String(500), nullable=False)  # 모델 파일 경로
    description = Column(Text)
    accuracy = Column(Float)  # 모델 정확도
    active = Column(Boolean, default=False)  # 현재 활성화된 모델인지
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    jobs = relationship("AIJob", back_populates="model")
    
    def to_dict(self):
        return {
            'model_id': self.model_id,
            'model_name': self.model_name,
            'version': self.version,
            'artifact_url': self.artifact_url,
            'description': self.description,
            'accuracy': self.accuracy,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }