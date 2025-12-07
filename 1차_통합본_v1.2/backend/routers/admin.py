"""
관리자 인증 및 관리 API 라우터
(통계 및 CSV 다운로드 기능 포함)
"""
import csv
import io
from datetime import datetime, timedelta
from fastapi.responses import StreamingResponse
from models.analysis import Analysis
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

# --------------------------------------------------------------------------
# 모델 및 서비스 Import
# --------------------------------------------------------------------------
from models.database import get_db
from models.admin import Admin
# ★ 중요: models/analysis.py 파일을 꼭 생성해야 아래 import가 작동합니다.
from models.analysis import Analysis 
from models.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminLogoutRequest,
    AdminLogoutResponse,
    InquiryReplyCreate
)
from services.admin_service import authenticate_admin, create_admin
from services.auth_service import create_access_token
from services import inquiry_service
from utils.dependencies import get_current_admin

router = APIRouter()

# --------------------------------------------------------------------------
# 1. 관리자 인증 (로그인/로그아웃)
# --------------------------------------------------------------------------

@router.post("/login", response_model=AdminLoginResponse)
def admin_login(
    request: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """
    관리자 로그인
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
    """
    return {
        "message": "관리자 대시보드에 오신 것을 환영합니다",
        "username": current_admin.username,
        "admin_id": current_admin.admin_id,
        "last_login_at": current_admin.last_login_at.isoformat() if current_admin.last_login_at else None
    }


# --------------------------------------------------------------------------
# 2. 데이터 분석 및 통계 관리
# --------------------------------------------------------------------------

# --- 데이터 관리 기능 추가 ---

@router.get("/stats")
def get_analysis_stats(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """대시보드 통계: 총 분석 수 및 금일 분석 수"""
    try:
        total_count = db.query(Analysis).count()
        
        today = datetime.now().date()
        today_count = db.query(Analysis).filter(Analysis.created_at >= today).count()
        
        return {
            "total_count": total_count, 
            "today_count": today_count
        }
    except Exception as e:
        print(f"통계 조회 오류: {e}")
        return {"total_count": 0, "today_count": 0}

@router.get("/download-csv")
def download_analysis_csv(
    start_date: str, 
    end_date: str, 
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    [관리자 기능] 기간별 분석 데이터 CSV 다운로드
    """
    try:
        # 1. 날짜 변환
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

        # 2. DB 조회
        results = db.query(Analysis).filter(
            Analysis.created_at >= start_dt,
            Analysis.created_at < end_dt
        ).all()

        # 3. CSV 생성 (메모리)
        stream = io.StringIO()
        
        # 엑셀 한글 깨짐 방지 (BOM 문자 추가)
        stream.write('\ufeff')

        csv_writer = csv.writer(stream)

        # 4. 헤더 작성
        csv_writer.writerow(["ID", "URL", "신뢰도 점수", "분석일시"])

        # 5. 데이터 작성
        for item in results:
            analysis_id_val = getattr(item, 'analysis_id', getattr(item, 'id', 'Unknown'))
            
            # 날짜를 보기 좋게 문자열로 변환 (YYYY-MM-DD HH:MM:SS)
            formatted_date = item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else ""

            csv_writer.writerow([
                analysis_id_val,
                item.review_url,
                item.confidence,
                formatted_date
            ])

        stream.seek(0)
        filename = f"analysis_data_{start_date}_{end_date}.csv"
        
        # 파일 응답 반환 (media_type을 ms-excel로 지정하면 엑셀이 더 잘 알아듣습니다)
        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        
        return response

    except Exception as e:
        print(f"❌ CSV 다운로드 오류: {e}")
        raise HTTPException(status_code=500, detail=f"CSV 생성 중 오류: {str(e)}")


@router.post("/create")
def create_admin_account(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """
    개발/테스트용: 관리자 계정 생성
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