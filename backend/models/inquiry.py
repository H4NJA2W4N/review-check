from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from models.database import Base


class Inquiry(Base):
    """사용자 문의 모델"""
    __tablename__ = "inquiries"

    inquiry_id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="문의 ID")
    user_id = Column(String(50), nullable=False, comment="문의한 사용자 ID")
    title = Column(String(200), nullable=False, comment="문의 제목")
    content = Column(Text, nullable=False, comment="문의 내용")
    status = Column(String(20), nullable=False, default="pending", comment="문의 상태 (pending / done)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="문의 생성일시")

    # 1:1 관계 (문의 1개에 답변 최대 1개)
    reply = relationship("InquiryReply", uselist=False, back_populates="inquiry", cascade="all, delete-orphan")