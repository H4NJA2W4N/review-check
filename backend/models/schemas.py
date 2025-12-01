from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ===== 관리자 인증 스키마 =====

class AdminLoginRequest(BaseModel):
    """관리자 로그인 요청"""
    username: str  # 로그인 아이디
    password: str  # 비밀번호

class AdminLoginResponse(BaseModel):
    """관리자 로그인 응답"""
    success: bool
    result_code: int  # 200: 성공, 401: 인증 실패, 422: 형식 오류
    message: str
    token: Optional[str] = None  # JWT 토큰
    expires_at: Optional[str] = None  # 토큰 만료 시간

class AdminLogoutRequest(BaseModel):
    """관리자 로그아웃 요청"""
    request_user: str  # 로그아웃을 요청한 관리자 아이디

class AdminLogoutResponse(BaseModel):
    """관리자 로그아웃 응답"""
    success: bool
    result_code: int  # 200: 성공, 600: 처리 실패
    message: str

class TokenData(BaseModel):
    """JWT 토큰 데이터"""
    username: str  # 관리자 username
    exp: datetime

# ===== 공지사항 스키마 =====

class AttachmentBase(BaseModel):
    """첨부파일 기본"""
    file_name: str
    file_url: str

class AttachmentResponse(AttachmentBase):
    """첨부파일 응답"""
    attachment_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class NoticeCreate(BaseModel):
    """공지사항 생성"""
    title: str
    content: str
    attachments: Optional[List[AttachmentBase]] = []

class NoticeUpdate(BaseModel):
    """공지사항 수정"""
    title: Optional[str] = None
    content: Optional[str] = None
    attachments: Optional[List[AttachmentBase]] = None

class NoticeResponse(BaseModel):
    """공지사항 응답"""
    notice_id: int
    admin_id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    attachments: List[AttachmentResponse] = []
    
    class Config:
        from_attributes = True

class NoticeListResponse(BaseModel):
    """공지사항 목록 응답"""
    success: bool
    result_code: int  # 200: 성공, 600: 오류
    items: List[NoticeResponse]
    total: int

class NoticeDetailResponse(BaseModel):
    """공지사항 상세 응답"""
    success: bool
    result_code: int  # 200: 성공, 404: 없음, 600: 오류
    notice: Optional[NoticeResponse] = None

class NoticeCreateResponse(BaseModel):
    """공지사항 생성 응답"""
    success: bool
    result_code: int  # 200: 성공, 600: 오류
    message: str
    notice: Optional[NoticeResponse] = None

class NoticeUpdateResponse(BaseModel):
    """공지사항 수정 응답"""
    success: bool
    result_code: int  # 200: 성공, 404: 없음, 600: 오류
    message: str
    notice: Optional[NoticeResponse] = None

class NoticeDeleteResponse(BaseModel):
    """공지사항 삭제 응답"""
    success: bool
    result_code: int  # 200: 성공, 404: 없음, 600: 오류
    message: str
    deleted: int

# ===== 문의 스키마 =====

class InquiryCreate(BaseModel):
    """사용자 문의 등록 요청"""
    user_id: str
    title: str
    content: str


class InquiryReplyCreate(BaseModel):
    """관리자 답변 등록/수정 요청"""
    content: str
    # 문서에는 content만 있지만, 필요하면 제목도 보낼 수 있게 옵션으로 둠
    title: Optional[str] = None


class InquiryReplyData(BaseModel):
    """문의 답변 정보"""
    reply_id: int
    inquiry_id: int
    admin_id: int
    title: str
    content: str
    replied_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InquiryDetailData(BaseModel):
    """문의 상세 정보"""
    inquiry_id: int
    user_id: str
    title: str
    content: str
    status: str
    created_at: datetime
    reply: Optional[InquiryReplyData] = None

    class Config:
        from_attributes = True


class InquirySummaryResponse(BaseModel):
    """문의 목록용 요약 정보"""
    inquiry_id: int
    user_id: str
    title: str
    status: str
    created_at: datetime
    has_reply: bool


class InquiryListResponse(BaseModel):
    """문의 목록 응답 (관리자)"""
    success: bool
    result_code: int  # 200: 성공, 600: 오류
    items: List[InquirySummaryResponse]
    total: int


class InquiryDetailResponse(BaseModel):
    """문의 상세 조회 응답 (관리자)"""
    success: bool
    result_code: int  # 200: 성공, 404: 없음, 600: 오류
    inquiry: Optional[InquiryDetailData] = None


class InquiryCreateResponse(BaseModel):
    """사용자 문의 등록 응답"""
    success: bool
    result_code: int  # 200: 성공, 600: 오류
    message: str
    inquiry: Optional[InquiryDetailData] = None


class InquiryReplyActionResponse(BaseModel):
    """답변 등록/수정/삭제 응답 (관리자)"""
    success: bool
    result_code: int  # 200: 성공, 404: 없음, 600: 오류
    message: str
    inquiry: Optional[InquiryDetailData] = None