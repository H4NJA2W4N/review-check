from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base

class Notice(Base):
    """공지사항 모델"""
    __tablename__ = "notices"

    notice_id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="공지사항 ID")
    admin_id = Column(Integer, ForeignKey("admins.admin_id"), nullable=False, comment="작성한 관리자 ID")
    title = Column(String(200), nullable=False, comment="제목")
    content = Column(Text, nullable=False, comment="내용")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정일시")
    
    # 관계 설정
    attachments = relationship("NoticeAttachment", back_populates="notice", cascade="all, delete-orphan")