"""
문의 API 라우터
- /user/inquiry: 사용자 문의 등록 (인증 불필요)
- /admin/inquiries: 관리자용 목록/상세/답변 (인증 필요)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from models.database import get_db
from models.admin import Admin
from models.schemas import (
    InquiryCreate,
    InquiryReplyCreate,
    InquirySummaryResponse,
    InquiryListResponse,
    InquiryDetailResponse,
    InquiryCreateResponse,
    InquiryReplyActionResponse,
    InquiryDetailData,
    InquiryReplyData,
)
from services.inquiry_service import (
    create_inquiry,
    get_inquiries,
    get_inquiry_by_id,
    create_or_update_reply,
    delete_reply_for_inquiry,
)
from utils.dependencies import get_current_admin

router = APIRouter()

# ===== 사용자용 API =====

@router.post("/user/inquiry", response_model=InquiryCreateResponse, tags=["사용자 문의"])
def create_user_inquiry(
    inquiry_data: InquiryCreate,
    db: Session = Depends(get_db),
):
    """
    사용자 문의 등록

    Body:
    - user_id: 사용자 ID
    - title: 제목
    - content: 내용
    """
    try:
        inquiry = create_inquiry(db, inquiry_data)

        detail = InquiryDetailData(
            inquiry_id=inquiry.inquiry_id,
            user_id=inquiry.user_id,
            title=inquiry.title,
            content=inquiry.content,
            status=inquiry.status,
            created_at=inquiry.created_at,
            reply=None,
        )

        return InquiryCreateResponse(
            success=True,
            result_code=200,
            message="문의가 성공적으로 등록되었습니다.",
            inquiry=detail,
        )
    except Exception as e:
        print(f"❌ 문의 등록 오류: {e}")
        return InquiryCreateResponse(
            success=False,
            result_code=600,
            message=f"문의 등록 중 오류가 발생했습니다: {str(e)}",
            inquiry=None,
        )

# ===== 관리자용 API =====

@router.get(
    "/admin/inquiries",
    response_model=InquiryListResponse,
    tags=["관리자 문의"],
)
def get_admin_inquiries(
    status: Optional[str] = Query(
        None, description="pending / done 상태 필터"
    ),
    q: Optional[str] = Query(
        None, description="제목/내용 검색어"
    ),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    문의 목록 조회 (관리자)

    Query:
    - status: pending / done (선택)
    - q: 제목/내용 검색어 (선택)
    - page: 페이지 번호 (기본 1)
    - size: 페이지 크기 (기본 20)
    """
    try:
        skip = (page - 1) * size
        inquiries, total = get_inquiries(
            db,
            skip=skip,
            limit=size,
            status=status,
            search_query=q,
        )

        items: list[InquirySummaryResponse] = []
        for inq in inquiries:
            items.append(
                InquirySummaryResponse(
                    inquiry_id=inq.inquiry_id,
                    user_id=inq.user_id,
                    title=inq.title,
                    status=inq.status,
                    created_at=inq.created_at,
                    has_reply=inq.reply is not None,
                )
            )

        return InquiryListResponse(
            success=True,
            result_code=200,
            items=items,
            total=total,
        )
    except Exception as e:
        print(f"❌ 문의 목록 조회 오류: {e}")
        return InquiryListResponse(
            success=False,
            result_code=600,
            items=[],
            total=0,
        )


@router.get(
    "/admin/inquiries/{inquiry_id}",
    response_model=InquiryDetailResponse,
    tags=["관리자 문의"],
)
def get_admin_inquiry_detail(
    inquiry_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    문의 상세 조회 (관리자)
    Path:
    - inquiry_id: 문의 ID
    """
    try:
        inquiry = get_inquiry_by_id(db, inquiry_id)
        if not inquiry:
            return InquiryDetailResponse(
                success=False,
                result_code=404,
                inquiry=None,
            )

        reply_obj = inquiry.reply
        reply = (
            InquiryReplyData(
                reply_id=reply_obj.reply_id,
                inquiry_id=reply_obj.inquiry_id,
                admin_id=reply_obj.admin_id,
                title=reply_obj.title,
                content=reply_obj.content,
                replied_at=reply_obj.replied_at,
                updated_at=reply_obj.updated_at,
            )
            if reply_obj
            else None
        )

        detail = InquiryDetailData(
            inquiry_id=inquiry.inquiry_id,
            user_id=inquiry.user_id,
            title=inquiry.title,
            content=inquiry.content,
            status=inquiry.status,
            created_at=inquiry.created_at,
            reply=reply,
        )

        return InquiryDetailResponse(
            success=True,
            result_code=200,
            inquiry=detail,
        )
    except Exception as e:
        print(f"❌ 문의 상세 조회 오류: {e}")
        return InquiryDetailResponse(
            success=False,
            result_code=600,
            inquiry=None,
        )


@router.post(
    "/admin/inquiries/{inquiry_id}/reply",
    response_model=InquiryReplyActionResponse,
    tags=["관리자 문의"],
)
def create_or_update_admin_reply(
    inquiry_id: int,
    reply_data: InquiryReplyCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    특정 문의에 대한 답변 등록/수정 (관리자)

    Path:
    - inquiry_id: 문의 ID

    Body:
    - content: 답변 내용
    - title: (선택) 답변 제목
    """
    try:
        inquiry, reply, created = create_or_update_reply(
            db, inquiry_id, current_admin.admin_id, reply_data
        )

        if not inquiry or not reply:
            return InquiryReplyActionResponse(
                success=False,
                result_code=404,
                message="문의를 찾을 수 없습니다.",
                inquiry=None,
            )

        reply_data_res = InquiryReplyData(
            reply_id=reply.reply_id,
            inquiry_id=reply.inquiry_id,
            admin_id=reply.admin_id,
            title=reply.title,
            content=reply.content,
            replied_at=reply.replied_at,
            updated_at=reply.updated_at,
        )

        detail = InquiryDetailData(
            inquiry_id=inquiry.inquiry_id,
            user_id=inquiry.user_id,
            title=inquiry.title,
            content=inquiry.content,
            status=inquiry.status,
            created_at=inquiry.created_at,
            reply=reply_data_res,
        )

        message = (
            "답변이 등록되었습니다."
            if created
            else "답변이 수정되었습니다."
        )

        return InquiryReplyActionResponse(
            success=True,
            result_code=200,
            message=message,
            inquiry=detail,
        )
    except Exception as e:
        print(f"❌ 답변 등록/수정 오류: {e}")
        return InquiryReplyActionResponse(
            success=False,
            result_code=600,
            message=f"답변 처리 중 오류가 발생했습니다: {str(e)}",
            inquiry=None,
        )


@router.delete(
    "/admin/inquiries/{inquiry_id}/reply",
    response_model=InquiryReplyActionResponse,
    tags=["관리자 문의"],
)
def delete_admin_reply(
    inquiry_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    특정 문의에 대한 답변 삭제 (관리자)

    Path:
    - inquiry_id: 문의 ID
    """
    try:
        inquiry = delete_reply_for_inquiry(db, inquiry_id)
        if not inquiry:
            return InquiryReplyActionResponse(
                success=False,
                result_code=404,
                message="삭제할 답변을 찾을 수 없습니다.",
                inquiry=None,
            )

        detail = InquiryDetailData(
            inquiry_id=inquiry.inquiry_id,
            user_id=inquiry.user_id,
            title=inquiry.title,
            content=inquiry.content,
            status=inquiry.status,  # pending 으로 되돌아감
            created_at=inquiry.created_at,
            reply=None,
        )

        return InquiryReplyActionResponse(
            success=True,
            result_code=200,
            message="답변이 삭제되었습니다.",
            inquiry=detail,
        )
    except Exception as e:
        print(f"❌ 답변 삭제 오류: {e}")
        return InquiryReplyActionResponse(
            success=False,
            result_code=600,
            message=f"답변 삭제 중 오류가 발생했습니다: {str(e)}",
            inquiry=None,
        )