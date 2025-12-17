"""
AI 작업(재학습 등) 관리 테이블
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class AIJob(Base):
    """AI 작업 관리 (재학습, 추론 등)"""
    __tablename__ = "ai_jobs"
    
    job_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_id = Column(Integer, ForeignKey('ai_models.model_id'), nullable=True)  # 사용할 모델
    submitted_by = Column(Integer, ForeignKey('admins.admin_id'), nullable=False)  # 작업 제출자
    type = Column(String(50), nullable=False)  # 'training', 'inference' 등
    status = Column(String(50), default='pending')  # 'pending', 'running', 'completed', 'failed'
    logs = Column(Text)  # 학습 로그
    error_message = Column(Text)  # 에러 메시지
    submitted_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    
    # Relationships
    model = relationship("AIModel", back_populates="jobs")
    admin = relationship("Admin")
    
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'model_id': self.model_id,
            'submitted_by': self.submitted_by,
            'type': self.type,
            'status': self.status,
            'logs': self.logs,
            'error_message': self.error_message,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None
        }