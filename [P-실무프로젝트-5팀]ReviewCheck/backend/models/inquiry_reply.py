from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from models.database import Base


class InquiryReply(Base):
    """문의 답변 모델"""
    __tablename__ = "inquiry_replies"

    reply_id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="답변 ID")
    inquiry_id = Column(Integer, ForeignKey("inquiries.inquiry_id", ondelete="CASCADE"), nullable=False, comment="문의 ID")
    admin_id = Column(Integer, ForeignKey("admins.admin_id"), nullable=False, comment="답변 작성 관리자 ID")
    title = Column(String(200), nullable=False, comment="답변 제목")
    content = Column(Text, nullable=False, comment="답변 내용")
    replied_at = Column(DateTime, default=datetime.utcnow, comment="답변 최초 작성일시")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="답변 수정일시")

    # 관계
    inquiry = relationship("Inquiry", back_populates="reply")