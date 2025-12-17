#
# JWT 토큰 검증을 위한 의존성 함수
#

from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from services.auth_service import extract_token_from_header, verify_token
from services.admin_service import get_admin_by_username
from models.database import get_db

def get_current_admin(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 관리자 정보 반환
    JWT 토큰 검증 의존성
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization 헤더가 필요합니다"
        )
    
    token = extract_token_from_header(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰 형식입니다"
        )
    
    username = verify_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않거나 만료된 토큰입니다"
        )
    
    admin = get_admin_by_username(db, username)
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="관리자를 찾을 수 없거나 비활성화되었습니다"
        )
    
    return admin