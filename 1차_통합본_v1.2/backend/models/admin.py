#
# 관리자용 User 모델
#

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from models.database import Base

class Admin(Base):
    """관리자 계정 모델"""
    __tablename__ = "admins"

    admin_id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="관리자 ID (PK)")
    username = Column(String(50), unique=True, index=True, nullable=False, comment="로그인 아이디")
    password_hash = Column(String(128), nullable=False, comment="해시된 비밀번호")
    last_login_at = Column(DateTime, nullable=True, comment="마지막 로그인 시간")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일시")
    is_active = Column(Boolean, default=True, comment="활성 상태")