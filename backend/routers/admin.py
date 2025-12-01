"""
관리자 인증 및 관리 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from models.database import get_db
from models.admin import Admin
from models.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminLogoutRequest,
    AdminLogoutResponse
)
from services.admin_service import authenticate_admin, create_admin
from services.auth_service import create_access_token
from utils.dependencies import get_current_admin

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(
    request: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """
    관리자 로그인
    
    - **username**: 관리자 아이디
    - **password**: 비밀번호
    
    Returns:
    - **success**: 처리 성공 여부
    - **result_code**: 200(성공), 401(인증 실패), 422(형식 오류)
    - **message**: 처리 결과 메시지
    - **token**: JWT 액세스 토큰
    - **expires_at**: 토큰 만료 시간
    """
    try:
        # 관리자 인증
        admin = authenticate_admin(db, request.username, request.password)
        
        if not admin:
            return AdminLoginResponse(
                success=False,
                result_code=401,
                message="관리자 아이디 또는 비밀번호가 일치하지 않습니다",
                token=None,
                expires_at=None
            )
        
        # JWT 토큰 생성
        token, expires_at = create_access_token(admin.username)
        
        print(f"✅ 관리자 로그인 성공: {admin.username}")
        
        return AdminLoginResponse(
            success=True,
            result_code=200,
            message="로그인에 성공했습니다",
            token=token,
            expires_at=expires_at.isoformat() + "Z"
        )
        
    except Exception as e:
        print(f"❌ 로그인 처리 오류: {e}")
        return AdminLoginResponse(
            success=False,
            result_code=422,
            message=f"로그인 처리 중 오류가 발생했습니다: {str(e)}",
            token=None,
            expires_at=None
        )


@router.post("/logout", response_model=AdminLogoutResponse)
def admin_logout(
    request: AdminLogoutRequest,
    authorization: str = Header(None),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    관리자 로그아웃
    
    Headers:
    - **Authorization**: Bearer {token}
    
    Body:
    - **request_user**: 로그아웃을 요청한 관리자 아이디
    
    Returns:
    - **success**: 처리 성공 여부
    - **result_code**: 200(성공), 600(처리 실패)
    - **message**: 처리 결과 메시지
    """
    try:
        if request.request_user != current_admin.username:
            return AdminLogoutResponse(
                success=False,
                result_code=600,
                message="요청 사용자와 토큰 사용자가 일치하지 않습니다"
            )
        
        print(f"✅ 관리자 로그아웃: {current_admin.username}")
        
        return AdminLogoutResponse(
            success=True,
            result_code=200,
            message="로그아웃에 성공했습니다"
        )
        
    except HTTPException as e:
        return AdminLogoutResponse(
            success=False,
            result_code=600,
            message=e.detail
        )
    except Exception as e:
        print(f"❌ 로그아웃 처리 오류: {e}")
        return AdminLogoutResponse(
            success=False,
            result_code=600,
            message=f"로그아웃 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/dashboard")
def admin_dashboard(current_admin: Admin = Depends(get_current_admin)):
    """
    관리자 대시보드 (보호된 엔드포인트)
    
    Headers:
    - **Authorization**: Bearer {token}
    """
    return {
        "message": "관리자 대시보드에 오신 것을 환영합니다",
        "username": current_admin.username,
        "admin_id": current_admin.admin_id,
        "last_login_at": current_admin.last_login_at.isoformat() if current_admin.last_login_at else None
    }


@router.post("/create")
def create_admin_account(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """
    개발/테스트용: 관리자 계정 생성
    
    ⚠️ 프로덕션에서는 이 엔드포인트를 제거하거나 보호해야 합니다
    """
    try:
        admin = create_admin(db, username, password)
        return {
            "success": True,
            "message": "관리자 계정이 생성되었습니다",
            "username": admin.username,
            "admin_id": admin.admin_id
        }
    except HTTPException as e:
        return {
            "success": False,
            "message": e.detail
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"계정 생성 오류: {str(e)}"
        }