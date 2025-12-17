#
# 관리자 인증 비즈니스 로직 서비스
#

from sqlalchemy.orm import Session
from datetime import datetime
from models.admin import Admin
from services.auth_service import hash_password, verify_password
from fastapi import HTTPException

def create_admin(db: Session, username: str, password: str) -> Admin:
    """
    관리자 계정 생성 (초기 설정용)
    """
    # 중복 체크
    existing = db.query(Admin).filter(Admin.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="관리자 아이디가 이미 존재합니다")
    
    # 관리자 생성
    hashed_pw = hash_password(password)
    db_admin = Admin(
        username=username,
        password_hash=hashed_pw,
        is_active=True
    )
    
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    
    print(f"✅ 관리자 생성: {username}")
    return db_admin

def authenticate_admin(db: Session, username: str, password: str) -> Admin | None:
    """
    관리자 인증
    Returns: Admin object or None
    """
    admin = db.query(Admin).filter(Admin.username == username).first()
    
    if not admin:
        print(f"❌ 관리자를 찾을 수 없음: {username}")
        return None
    
    if not admin.is_active:
        print(f"❌ 비활성화된 관리자: {username}")
        return None
    
    if not verify_password(password, admin.password_hash):
        print(f"❌ 비밀번호 불일치: {username}")
        return None
    
    # 마지막 로그인 시간 업데이트
    admin.last_login_at = datetime.utcnow()
    db.commit()
    
    print(f"✅ 관리자 인증 성공: {username}")
    return admin

def get_admin_by_username(db: Session, username: str) -> Admin | None:
    """username으로 관리자 조회"""
    return db.query(Admin).filter(Admin.username == username).first()