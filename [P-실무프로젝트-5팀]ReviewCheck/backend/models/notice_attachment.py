from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base

class NoticeAttachment(Base):
    """공지사항 첨부파일 모델"""
    __tablename__ = "notices_attachments"

    attachment_id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="첨부파일 ID")
    notice_id = Column(Integer, ForeignKey("notices.notice_id", ondelete="CASCADE"), nullable=False, comment="공지사항 ID")
    file_name = Column(String(255), nullable=False, comment="파일명")
    file_url = Column(String(500), nullable=False, comment="파일 URL")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일시")
    
    # 관계 설정
    notice = relationship("Notice", back_populates="attachments")