"""
크롤링 API 라우터 (선택적)
크롤링만 별도로 사용하고 싶을 때 활용
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from models.database import get_db
from services.musinsa_api_crawler import MusinsaCrawler
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crawl", tags=["크롤링"])


# ===== Request/Response 모델 =====

class CrawlRequest(BaseModel):
    """크롤링 요청"""
    product_url: str = Field(..., description="무신사 상품 URL")
    max_reviews: int = Field(100, description="최대 크롤링 리뷰 수")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_url": "https://www.musinsa.com/products/3242941",
                "max_reviews": 100
            }
        }


class CrawlResponse(BaseModel):
    """크롤링 응답"""
    success: bool
    message: str
    product_id: str = None
    product_url: str
    raw_count: int
    filtered_count: int
    reviews: list = []


# ===== API 엔드포인트 =====

@router.post("/", response_model=CrawlResponse)
async def crawl_reviews(
    request: CrawlRequest
):
    """
    무신사 리뷰 크롤링
    
    - 무신사 상품 URL을 입력받아 리뷰를 크롤링합니다
    - 분석 없이 크롤링만 수행합니다
    
    **사용 예시:**
    ```python
    # 크롤링만 (DB 저장 안 함)
    POST /crawl
    {
      "product_url": "https://www.musinsa.com/products/3242941",
      "max_reviews": 100
    }
    
    # 크롤링 + DB 저장
    POST /crawl
    {
      "product_url": "https://www.musinsa.com/products/3242941",
      "max_reviews": 100
    }
    ```
    """
    try:
        logger.info(f"크롤링 요청: {request.product_url}, max={request.max_reviews}")
        
        # 크롤링 실행
        crawler = MusinsaCrawler()
        result = crawler.crawl_reviews(
            product_url=request.product_url,
            max_reviews=request.max_reviews
        )
        
        # 응답 구성
        response = CrawlResponse(
            success=result['success'],
            message=result['message'],
            product_id=result['product_id'],
            product_url=result['product_url'],
            raw_count=result['raw_count'],
            filtered_count=result['filtered_count'],
            reviews=result['reviews']
        )
        
        logger.info(f"크롤링 완료: {result['filtered_count']}개")
        
        return response
        
    except Exception as e:
        logger.error(f"크롤링 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"크롤링 중 오류가 발생했습니다: {str(e)}")


# @router.get("/reviews/{product_id}")
# async def get_reviews_from_db(
#     product_id: str,
#     limit: int = 100,
#     db: Session = Depends(get_db)
# ):
#     """
#     DB에서 크롤링된 리뷰 조회
    
#     - 이전에 크롤링하여 DB에 저장된 리뷰를 조회합니다
#     - product_id로 필터링합니다
#     """
#     try:
#         reviews = MusinsaCrawler.get_from_db(
#             db=db,
#             product_id=product_id,
#             limit=limit
#         )
        
#         return {
#             'success': True,
#             'product_id': product_id,
#             'count': len(reviews),
#             'reviews': reviews
#         }
        
#     except Exception as e:
#         logger.error(f"리뷰 조회 오류: {e}")
#         raise HTTPException(status_code=500, detail=f"리뷰 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/health")
async def health_check():
    """크롤링 서비스 헬스 체크"""
    return {
        "status": "healthy",
        "service": "crawling-service",
        "message": "크롤링 서비스가 정상 작동 중입니다."
    }