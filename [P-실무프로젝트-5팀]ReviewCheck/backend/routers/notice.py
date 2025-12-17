"""
공지사항 API 라우터
- /user/notices: 사용자용 (인증 불필요)
- /admin/notices: 관리자용 (인증 필요)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from models.database import get_db
from models.admin import Admin
from models.schemas import (
    NoticeCreate,
    NoticeUpdate,
    NoticeListResponse,
    NoticeDetailResponse,
    NoticeCreateResponse,
    NoticeUpdateResponse,
    NoticeDeleteResponse,
    NoticeResponse,
    AttachmentResponse
)
from services.notice_service import (
    create_notice,
    get_notice_by_id,
    get_notices,
    update_notice,
    delete_notice,
    delete_notices_bulk
)
from utils.dependencies import get_current_admin

router = APIRouter()

# ===== 사용자용 API (인증 불필요) =====

@router.get("/user/notices", response_model=NoticeListResponse, tags=["사용자 공지사항"])
def get_user_notices(
    q: Optional[str] = Query(None, description="검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db)
):
    """
    공지사항 목록 조회 (사용자)
    
    - **q**: 검색어 (제목/내용 검색)
    - **page**: 페이지 번호 (기본 1)
    - **size**: 페이지 크기 (기본 20)
    """
    try:
        skip = (page - 1) * size
        notices, total = get_notices(db, skip=skip, limit=size, search_query=q)
        
        # 응답 데이터 변환
        items = []
        for notice in notices:
            attachments = [
                AttachmentResponse(
                    attachment_id=att.attachment_id,
                    file_name=att.file_name,
                    file_url=att.file_url,
                    created_at=att.created_at
                )
                for att in notice.attachments
            ]
            
            items.append(NoticeResponse(
                notice_id=notice.notice_id,
                admin_id=notice.admin_id,
                title=notice.title,
                content=notice.content,
                created_at=notice.created_at,
                updated_at=notice.updated_at,
                attachments=attachments
            ))
        
        return NoticeListResponse(
            success=True,
            result_code=200,
            items=items,
            total=total
        )
    except Exception as e:
        print(f"❌ 공지사항 목록 조회 오류: {e}")
        return NoticeListResponse(
            success=False,
            result_code=600,
            items=[],
            total=0
        )

@router.get("/user/notices/{notice_id}", response_model=NoticeDetailResponse, tags=["사용자 공지사항"])
def get_user_notice(
    notice_id: int,
    db: Session = Depends(get_db)
):
    """
    공지사항 상세 조회 (사용자)
    
    - **notice_id**: 공지사항 ID
    """
    try:
        notice = get_notice_by_id(db, notice_id)
        
        if not notice:
            return NoticeDetailResponse(
                success=False,
                result_code=404,
                notice=None
            )
        
        # 첨부파일 변환
        attachments = [
            AttachmentResponse(
                attachment_id=att.attachment_id,
                file_name=att.file_name,
                file_url=att.file_url,
                created_at=att.created_at
            )
            for att in notice.attachments
        ]
        
        return NoticeDetailResponse(
            success=True,
            result_code=200,
            notice=NoticeResponse(
                notice_id=notice.notice_id,
                admin_id=notice.admin_id,
                title=notice.title,
                content=notice.content,
                created_at=notice.created_at,
                updated_at=notice.updated_at,
                attachments=attachments
            )
        )
    except Exception as e:
        print(f"❌ 공지사항 조회 오류: {e}")
        return NoticeDetailResponse(
            success=False,
            result_code=600,
            notice=None
        )

# ===== 관리자용 API (인증 필요) =====

@router.get("/admin/notices", response_model=NoticeListResponse, tags=["관리자 공지사항"])
def get_admin_notices(
    q: Optional[str] = Query(None, description="검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    공지사항 목록 조회 (관리자)
    
    Headers:
    - **Authorization**: Bearer {token}
    
    Query:
    - **q**: 검색어
    - **page**: 페이지 번호
    - **size**: 페이지 크기
    """
    try:
        skip = (page - 1) * size
        notices, total = get_notices(db, skip=skip, limit=size, search_query=q)
        
        items = []
        for notice in notices:
            attachments = [
                AttachmentResponse(
                    attachment_id=att.attachment_id,
                    file_name=att.file_name,
                    file_url=att.file_url,
                    created_at=att.created_at
                )
                for att in notice.attachments
            ]
            
            items.append(NoticeResponse(
                notice_id=notice.notice_id,
                admin_id=notice.admin_id,
                title=notice.title,
                content=notice.content,
                created_at=notice.created_at,
                updated_at=notice.updated_at,
                attachments=attachments
            ))
        
        return NoticeListResponse(
            success=True,
            result_code=200,
            items=items,
            total=total
        )
    except Exception as e:
        print(f"❌ 공지사항 목록 조회 오류: {e}")
        return NoticeListResponse(
            success=False,
            result_code=600,
            items=[],
            total=0
        )

@router.get("/admin/notices/{notice_id}", response_model=NoticeDetailResponse, tags=["관리자 공지사항"])
def get_admin_notice(
    notice_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    공지사항 상세 조회 (관리자)
    
    Headers:
    - **Authorization**: Bearer {token}
    """
    try:
        notice = get_notice_by_id(db, notice_id)
        
        if not notice:
            return NoticeDetailResponse(
                success=False,
                result_code=404,
                notice=None
            )
        
        attachments = [
            AttachmentResponse(
                attachment_id=att.attachment_id,
                file_name=att.file_name,
                file_url=att.file_url,
                created_at=att.created_at
            )
            for att in notice.attachments
        ]
        
        return NoticeDetailResponse(
            success=True,
            result_code=200,
            notice=NoticeResponse(
                notice_id=notice.notice_id,
                admin_id=notice.admin_id,
                title=notice.title,
                content=notice.content,
                created_at=notice.created_at,
                updated_at=notice.updated_at,
                attachments=attachments
            )
        )
    except Exception as e:
        print(f"❌ 공지사항 조회 오류: {e}")
        return NoticeDetailResponse(
            success=False,
            result_code=600,
            notice=None
        )

@router.post("/admin/notices", response_model=NoticeCreateResponse, tags=["관리자 공지사항"])
def create_admin_notice(
    notice_data: NoticeCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    공지사항 생성 (관리자)
    
    Headers:
    - **Authorization**: Bearer {token}
    
    Body:
    - **title**: 제목
    - **content**: 내용
    - **attachments**: 첨부파일 목록 (선택)
    """
    try:
        db_notice = create_notice(db, current_admin.admin_id, notice_data)
        
        attachments = [
            AttachmentResponse(
                attachment_id=att.attachment_id,
                file_name=att.file_name,
                file_url=att.file_url,
                created_at=att.created_at
            )
            for att in db_notice.attachments
        ]
        
        return NoticeCreateResponse(
            success=True,
            result_code=200,
            message="공지사항이 성공적으로 등록되었습니다",
            notice=NoticeResponse(
                notice_id=db_notice.notice_id,
                admin_id=db_notice.admin_id,
                title=db_notice.title,
                content=db_notice.content,
                created_at=db_notice.created_at,
                updated_at=db_notice.updated_at,
                attachments=attachments
            )
        )
    except Exception as e:
        print(f"❌ 공지사항 생성 오류: {e}")
        return NoticeCreateResponse(
            success=False,
            result_code=600,
            message=f"공지사항 생성 중 오류가 발생했습니다: {str(e)}",
            notice=None
        )

@router.put("/admin/notices/{notice_id}", response_model=NoticeUpdateResponse, tags=["관리자 공지사항"])
def update_admin_notice(
    notice_id: int,
    notice_data: NoticeUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    공지사항 수정 (관리자)
    
    Headers:
    - **Authorization**: Bearer {token}
    
    Body:
    - **title**: 제목 (선택)
    - **content**: 내용 (선택)
    - **attachments**: 첨부파일 목록 (선택)
    """
    try:
        db_notice = update_notice(db, notice_id, notice_data)
        
        if not db_notice:
            return NoticeUpdateResponse(
                success=False,
                result_code=404,
                message="공지사항을 찾을 수 없습니다",
                notice=None
            )
        
        attachments = [
            AttachmentResponse(
                attachment_id=att.attachment_id,
                file_name=att.file_name,
                file_url=att.file_url,
                created_at=att.created_at
            )
            for att in db_notice.attachments
        ]
        
        return NoticeUpdateResponse(
            success=True,
            result_code=200,
            message="공지사항이 성공적으로 수정되었습니다",
            notice=NoticeResponse(
                notice_id=db_notice.notice_id,
                admin_id=db_notice.admin_id,
                title=db_notice.title,
                content=db_notice.content,
                created_at=db_notice.created_at,
                updated_at=db_notice.updated_at,
                attachments=attachments
            )
        )
    except Exception as e:
        print(f"❌ 공지사항 수정 오류: {e}")
        return NoticeUpdateResponse(
            success=False,
            result_code=600,
            message=f"공지사항 수정 중 오류가 발생했습니다: {str(e)}",
            notice=None
        )

@router.delete("/admin/notices/{notice_id}", response_model=NoticeDeleteResponse, tags=["관리자 공지사항"])
def delete_admin_notice(
    notice_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    공지사항 삭제 (관리자) - 단건
    
    Headers:
    - **Authorization**: Bearer {token}
    """
    try:
        success = delete_notice(db, notice_id)
        
        if not success:
            return NoticeDeleteResponse(
                success=False,
                result_code=404,
                message="공지사항을 찾을 수 없습니다",
                deleted=0
            )
        
        return NoticeDeleteResponse(
            success=True,
            result_code=200,
            message="공지사항이 성공적으로 삭제되었습니다",
            deleted=1
        )
    except Exception as e:
        print(f"❌ 공지사항 삭제 오류: {e}")
        return NoticeDeleteResponse(
            success=False,
            result_code=600,
            message=f"공지사항 삭제 중 오류가 발생했습니다: {str(e)}",
            deleted=0
        )

@router.delete("/admin/notices", response_model=NoticeDeleteResponse, tags=["관리자 공지사항"])
def delete_admin_notices_bulk(
    ids: List[int] = Query(..., description="삭제할 공지사항 ID 리스트"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    공지사항 삭제 (관리자) - 복수
    
    Headers:
    - **Authorization**: Bearer {token}
    
    Query:
    - **ids**: 삭제할 공지사항 ID 리스트
    
    예시: DELETE /admin/notices?ids=1&ids=2&ids=3
    """
    try:
        deleted_count = delete_notices_bulk(db, ids)
        
        if deleted_count == 0:
            return NoticeDeleteResponse(
                success=False,
                result_code=404,
                message="삭제할 공지사항을 찾을 수 없습니다",
                deleted=0
            )
        
        return NoticeDeleteResponse(
            success=True,
            result_code=200,
            message=f"{deleted_count}개의 공지사항이 성공적으로 삭제되었습니다",
            deleted=deleted_count
        )
    except Exception as e:
        print(f"❌ 공지사항 삭제 오류: {e}")
        return NoticeDeleteResponse(
            success=False,
            result_code=600,
            message=f"공지사항 삭제 중 오류가 발생했습니다: {str(e)}",
            deleted=0
        )