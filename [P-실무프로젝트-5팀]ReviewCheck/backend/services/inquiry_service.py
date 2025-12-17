from sqlalchemy.orm import Session, joinedload
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
    return (
        db.query(Inquiry)
        .options(joinedload(Inquiry.reply))  # 답변 데이터도 같이 가져옴
        .filter(Inquiry.inquiry_id == inquiry_id)
        .first()
    )


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
    query = db.query(Inquiry).options(joinedload(Inquiry.reply))

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

def get_inquiries_by_user(db: Session, user_identifier: str):
    """
    특정 사용자(이메일 또는 user_id로 쓰는 식별자)의 문의 목록 반환.
    - user_identifier: 프론트에서 보내는 user_id (현재 이메일로 보내므로 문자열로 처리)
    """
    # user_id 칼럼이 문자열을 허용한다고 가정.
    query = db.query(Inquiry).options(joinedload(Inquiry.reply)).filter(Inquiry.user_id == user_identifier)
    inquiries = query.order_by(Inquiry.created_at.desc()).all()
    return inquiries

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
    # 생성된 답변 객체를 반환하기 위해 (만약 created=True일 때 inquiry.reply가 즉시 반영 안 될 경우 대비)
    if created:
         # 방금 만든 답변을 가져오기 위한 안전 장치
         # (InquiryReply 모델에서 직접 조회하거나, inquiry를 다시 refresh)
         db_reply = db.query(InquiryReply).filter(InquiryReply.inquiry_id == inquiry_id).first()
         return inquiry, db_reply, created
         
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
    
    # 관계 끊기 및 상태 복구
    # (JPA의 orphanRemoval과 달리 SQLAlchemy는 명시적 삭제가 안전)
    inquiry.status = "pending"

    db.commit()
    db.refresh(inquiry)
    return inquiry