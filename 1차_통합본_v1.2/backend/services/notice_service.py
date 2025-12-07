from sqlalchemy.orm import Session
from typing import List, Optional
from models.notice import Notice
from models.notice_attachment import NoticeAttachment
from models.schemas import NoticeCreate, NoticeUpdate, AttachmentBase

def create_notice(db: Session, admin_id: int, notice_data: NoticeCreate) -> Notice:
    """공지사항 생성"""
    # 공지사항 생성
    db_notice = Notice(
        admin_id=admin_id,
        title=notice_data.title,
        content=notice_data.content
    )
    db.add(db_notice)
    db.flush()  # notice_id 생성을 위해 flush
    
    # 첨부파일 추가
    if notice_data.attachments:
        for attachment in notice_data.attachments:
            db_attachment = NoticeAttachment(
                notice_id=db_notice.notice_id,
                file_name=attachment.file_name,
                file_url=attachment.file_url
            )
            db.add(db_attachment)
    
    db.commit()
    db.refresh(db_notice)
    return db_notice

def get_notice_by_id(db: Session, notice_id: int) -> Optional[Notice]:
    """공지사항 조회"""
    return db.query(Notice).filter(Notice.notice_id == notice_id).first()

def get_notices(
    db: Session, 
    skip: int = 0, 
    limit: int = 20, 
    search_query: Optional[str] = None
) -> tuple[List[Notice], int]:
    """공지사항 목록 조회 (페이지네이션 + 검색)"""
    query = db.query(Notice)
    
    # 검색어가 있으면 제목 또는 내용에서 검색
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            (Notice.title.like(search_pattern)) | 
            (Notice.content.like(search_pattern))
        )
    
    total = query.count()
    notices = query.order_by(Notice.created_at.desc()).offset(skip).limit(limit).all()
    
    return notices, total

def update_notice(
    db: Session, 
    notice_id: int, 
    notice_update: NoticeUpdate
) -> Optional[Notice]:
    """공지사항 수정"""
    db_notice = db.query(Notice).filter(Notice.notice_id == notice_id).first()
    
    if not db_notice:
        return None
    
    # 제목/내용 수정
    if notice_update.title is not None:
        db_notice.title = notice_update.title
    if notice_update.content is not None:
        db_notice.content = notice_update.content
    
    # 첨부파일 수정 (기존 삭제 후 새로 추가)
    if notice_update.attachments is not None:
        # 기존 첨부파일 삭제
        db.query(NoticeAttachment).filter(
            NoticeAttachment.notice_id == notice_id
        ).delete()
        
        # 새 첨부파일 추가
        for attachment in notice_update.attachments:
            db_attachment = NoticeAttachment(
                notice_id=notice_id,
                file_name=attachment.file_name,
                file_url=attachment.file_url
            )
            db.add(db_attachment)
    
    db.commit()
    db.refresh(db_notice)
    return db_notice

def delete_notice(db: Session, notice_id: int) -> bool:
    """공지사항 삭제 (단건)"""
    db_notice = db.query(Notice).filter(Notice.notice_id == notice_id).first()
    
    if not db_notice:
        return False
    
    db.delete(db_notice)
    db.commit()
    return True

def delete_notices_bulk(db: Session, notice_ids: List[int]) -> int:
    """공지사항 삭제 (복수)"""
    deleted_count = db.query(Notice).filter(
        Notice.notice_id.in_(notice_ids)
    ).delete(synchronize_session=False)
    
    db.commit()
    return deleted_count