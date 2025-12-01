from sqlalchemy.orm import Session
from typing import Optional, Tuple, List
from datetime import datetime

from models.inquiry import Inquiry
from models.inquiry_reply import InquiryReply
from models.schemas import InquiryCreate, InquiryReplyCreate


def create_inquiry(db: Session, inquiry_data: InquiryCreate) -> Inquiry:
    """사용자 문의 생성"""
    db_inquiry = Inquiry(
        user_id=inquiry_data.user_id,
        title=inquiry_data.title,
        content=inquiry_data.content,
        status="pending",
    )
    db.add(db_inquiry)
    db.commit()
    db.refresh(db_inquiry)
    return db_inquiry


def get_inquiry_by_id(db: Session, inquiry_id: int) -> Optional[Inquiry]:
    """문의 단건 조회"""
    return db.query(Inquiry).filter(Inquiry.inquiry_id == inquiry_id).first()


def get_inquiries(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    search_query: Optional[str] = None,
) -> Tuple[List[Inquiry], int]:
    """
    문의 목록 조회 (페이지네이션 + 상태 필터 + 검색어)
    - status: "pending" / "done" / None
    - search_query: 제목/내용 검색
    """
    query = db.query(Inquiry)

    if status in ("pending", "done"):
        query = query.filter(Inquiry.status == status)

    if search_query:
        pattern = f"%{search_query}%"
        query = query.filter(
            (Inquiry.title.like(pattern)) | (Inquiry.content.like(pattern))
        )

    total = query.count()
    inquiries = (
        query.order_by(Inquiry.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return inquiries, total


def create_or_update_reply(
    db: Session,
    inquiry_id: int,
    admin_id: int,
    reply_data: InquiryReplyCreate,
) -> Tuple[Optional[Inquiry], Optional[InquiryReply], bool]:
    """
    문의에 대한 답변 생성 또는 수정
    Returns: (Inquiry, InquiryReply, created_flag)
    - created_flag = True 이면 새로 생성, False 이면 수정
    """
    inquiry = get_inquiry_by_id(db, inquiry_id)
    if not inquiry:
        return None, None, False

    # 기존 답변이 있는 경우 -> 수정
    if inquiry.reply:
        inquiry.reply.content = reply_data.content
        if reply_data.title is not None:
            inquiry.reply.title = reply_data.title
        inquiry.reply.updated_at = datetime.utcnow()
        created = False
    else:
        # 새 답변 생성
        title = reply_data.title or f"[답변] {inquiry.title}"
        reply = InquiryReply(
            inquiry_id=inquiry.inquiry_id,
            admin_id=admin_id,
            title=title,
            content=reply_data.content,
        )
        db.add(reply)
        # relationship 통해 연결
        inquiry.reply = reply
        created = True

    # 상태를 done으로 변경
    inquiry.status = "done"

    db.commit()
    db.refresh(inquiry)
    # refresh 후 inquiry.reply가 최신 상태
    return inquiry, inquiry.reply, created


def delete_reply_for_inquiry(
    db: Session, inquiry_id: int
) -> Optional[Inquiry]:
    """
    문의에 달린 답변 삭제
    - 답변 삭제 후 문의 상태를 pending으로 되돌림
    """
    inquiry = get_inquiry_by_id(db, inquiry_id)
    if not inquiry or not inquiry.reply:
        return None

    # reply 객체 삭제
    db.delete(inquiry.reply)
    inquiry.reply = None
    inquiry.status = "pending"

    db.commit()
    db.refresh(inquiry)
    return inquiry