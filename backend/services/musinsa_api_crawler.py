"""
무신사 리뷰 크롤링 서비스 (통합)

모든 크롤링 관련 기능을 하나로 통합:
- URL 유효성 검사
- API 호출 및 파싱
- 리뷰 필터링
- DB 저장/조회
"""
from sqlalchemy.orm import Session
import re
import time
import json
import requests
from typing import List, Dict, Optional
import logging
logger = logging.getLogger(__name__)


class MusinsaCrawler:
    """무신사 리뷰 크롤러 (All-in-One)"""
    
    # 무신사 API 엔드포인트
    API_BASE_URL = "https://goods.musinsa.com/api2/review/v1/view/list"
    
    def __init__(self):
        """크롤러 초기화"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Origin': 'https://www.musinsa.com',
            'Referer': 'https://www.musinsa.com/',
        })
    
    # ===== URL 유효성 검사 =====
    
    @staticmethod
    def validate_url(url: str) -> tuple[bool, str, str]:
        """
        무신사 URL 유효성 검사
        
        Args:
            url: 무신사 상품 URL
        
        Returns:
            (유효 여부, 에러 메시지, 상품 ID)
        """
        if not url:
            return False, "URL이 비어있습니다.", None
        
        # 무신사 URL 패턴 체크
        pattern = r'https?://(?:www\.)?musinsa\.com/products/(\d+)'
        match = re.match(pattern, url)
        
        if not match:
            return False, "올바른 무신사 상품 URL이 아닙니다. (예: https://www.musinsa.com/products/3242941)", None
        
        product_id = match.group(1)
        return True, "", product_id
    
    def extract_product_id(self, url: str) -> Optional[str]:
        """
        URL에서 상품 ID 추출
        예: https://www.musinsa.com/products/3242941 -> 3242941
        """
        match = re.search(r'/products/(\d+)', url)
        return match.group(1) if match else None
    
    # ===== API 호출 =====
    
    def fetch_reviews_page(
        self, 
        goods_no: str, 
        page: int = 0, 
        page_size: int = 100,
        sort: str = "up_cnt_desc"
    ) -> Dict:
        """
        특정 페이지의 리뷰 가져오기
        
        Args:
            goods_no: 상품 번호
            page: 페이지 번호 (0부터)
            page_size: 한 번에 가져올 리뷰 수 (최대 100)
            sort: 정렬 방식
                - up_cnt_desc: 도움됨 순
                - reg_dt_desc: 최신순
                - grade_desc: 별점 높은순
                - grade_asc: 별점 낮은순
        
        Returns:
            API 응답 JSON
        """
        params = {
            'page': page,
            'pageSize': page_size,
            'goodsNo': goods_no,
            'sort': sort,
            'selectedSimilarNo': goods_no,
            'myFilter': 'false',
            'hasPhoto': 'false',
            'isExperience': 'false'
        }
        
        try:
            response = self.session.get(
                self.API_BASE_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API 요청 실패 (page={page}): {e}")
            raise
    
    # ===== 리뷰 파싱 =====
    
    @staticmethod
    def parse_review(review_data: Dict) -> Dict:
        """
        API 응답에서 리뷰 데이터 파싱
        
        Args:
            review_data: API 응답의 개별 리뷰 데이터
        
        Returns:
            파싱된 리뷰 딕셔너리
        """
        return {
            'review_id': review_data.get('no'),
            'text': (review_data.get('content') or '').strip(),
            # grade가 문자열 "5"로 오더라도 int로 변환해서 저장
            'rating': int(review_data.get('grade')) if review_data.get('grade') is not None else None,
            'author': review_data.get('userProfileInfo', {}).get('userNickName'),
            'author_profile': review_data.get('userImageFile'),
            'date': review_data.get('createDate'),
            'helpful_count': review_data.get('likeCount', 0),
            'unhelpful_count': 0,  # 응답에 따로 없으니 0으로
            'product_info': review_data.get('goodsOption'),
            'has_photo': False,
            'photo_urls': [],
            # 프로필에 키/몸무게가 있을 경우
            'body_shape': None,
            'height': None,
            'weight': None,
    }
    
    # ===== 리뷰 필터링 =====
    
    @staticmethod
    def clean_text(text: str) -> str:
        """리뷰 텍스트 정제"""
        if not text:
            return ""
        
        # 공백 정리
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def filter_meaningful_reviews(reviews: List[Dict], min_length: int = 10) -> List[Dict]:
        """
        의미 있는 리뷰만 필터링
        
        Args:
            reviews: 원본 리뷰 리스트
            min_length: 최소 텍스트 길이
        
        Returns:
            필터링된 리뷰 리스트
        """
        filtered = []
        
        for review in reviews:
            text = review.get('text', '')
            
            # 최소 길이 체크
            if len(text) < min_length:
                continue
            
            # 의미 없는 리뷰 패턴 제거
            meaningless_patterns = [
                r'^[ㅋㅎㅇ\s]+$',  # 'ㅋㅋㅋ', 'ㅎㅎㅎ' 등
                r'^[!?.]+$',  # 특수문자만
            ]
            
            is_meaningless = any(re.match(pattern, text) for pattern in meaningless_patterns)
            
            if not is_meaningless:
                review['text'] = MusinsaCrawler.clean_text(text)
                filtered.append(review)
        
        return filtered
    
    # ===== 크롤링 메인 로직 =====
    
    def crawl_all_reviews(
        self, 
        goods_no: str, 
        max_reviews: Optional[int] = None,
        page_size: int = 100,
        sort: str = "up_cnt_desc"
    ) -> List[Dict]:
        """
        모든 리뷰 가져오기 (페이지네이션 자동)
        
        Args:
            goods_no: 상품 번호
            max_reviews: 최대 크롤링 리뷰 수 (None이면 전체)
            page_size: 페이지당 리뷰 수
            sort: 정렬 방식
        
        Returns:
            리뷰 리스트
        """
        
        all_reviews = []
        page = 0
        
        logger.info(f"[MusinsaCrawler] 상품 {goods_no} 크롤링 시작")
        
        while True:
            try:
                # API 호출
                logger.debug(f"페이지 {page} 요청 중...")
                response_data = self.fetch_reviews_page(
                    goods_no=goods_no,
                    page=page,
                    page_size=page_size,
                    sort=sort
                )
                
                # 리뷰 데이터 추출
                data = response_data.get('data', {}) or {}
                reviews = data.get('list', [])
                total_count = data.get('totalCount') or data.get('totalCnt') or 0
                
                if not reviews:
                    logger.info(f"더 이상 리뷰 없음 (총 {len(all_reviews)}개 수집)")
                    break
                
                # 리뷰 파싱
                for review_data in reviews:
                    parsed = self.parse_review(review_data)
                    if parsed['text']:  # 텍스트가 있는 리뷰만
                        all_reviews.append(parsed)
                
                logger.debug(f"페이지 {page}: {len(reviews)}개 (누적: {len(all_reviews)}/{total_count})")
                
                # 최대 리뷰 수 체크
                if max_reviews and len(all_reviews) >= max_reviews:
                    all_reviews = all_reviews[:max_reviews]
                    logger.info(f"최대 리뷰 수 도달: {max_reviews}개")
                    break
                
                # 모든 리뷰 수집 완료
                if len(all_reviews) >= total_count:
                    logger.info(f"모든 리뷰 수집 완료: {len(all_reviews)}개")
                    break
                
                # 다음 페이지
                page += 1
                time.sleep(0.3)  # API 부하 방지
                
            except Exception as e:
                logger.error(f"페이지 {page} 크롤링 실패: {e}")
                break
        
        return all_reviews
    
    def crawl_reviews(
        self, 
        product_url: str, 
        max_reviews: Optional[int] = None,
    ) -> Dict:
        """
        무신사 리뷰 크롤링 메인 함수
        
        Args:
            product_url: 무신사 상품 URL
            max_reviews: 최대 크롤링 리뷰 수
        
        Returns:
            {
                'success': bool,
                'message': str,
                'product_id': str,
                'product_url': str,
                'reviews': List[Dict],
                'raw_count': int,
                'filtered_count': int
            }
        """
        result = {
            'success': False,
            'message': '',
            'product_id': None,
            'product_url': product_url,
            'reviews': [],
            'raw_count': 0,
            'filtered_count': 0
        }
        
        try:
            # 1. URL 유효성 검사
            is_valid, error_msg, product_id = self.validate_url(product_url)
            if not is_valid:
                result['message'] = error_msg
                return result
            
            result['product_id'] = product_id
            logger.info(f"[MusinsaCrawler] 상품 {product_id} 크롤링 시작")
            
            # 2. 모든 리뷰 수집
            raw_reviews = self.crawl_all_reviews(
                goods_no=product_id,
                max_reviews=max_reviews,
                page_size=100
            )

            for idx, rv in enumerate(raw_reviews[:3]):
                logger.info(f"[Sample Review {idx+1}] {rv.get('text')[:50]!r}")

            logger.info(f"[MusinsaCrawler] 상품 {product_id} 크롤링 결과: raw_reviews={len(raw_reviews)}")
            # 3. 리뷰 필터링
            filtered_reviews = raw_reviews
            # filtered_reviews = self.filter_meaningful_reviews(raw_reviews, min_length=10)
            
            logger.info(f"[MusinsaCrawler] 완료: raw={len(raw_reviews)}, filtered={len(filtered_reviews)}")
            
            # 4. 결과 반환
            result.update({
                'success': True,
                'message': f'{len(filtered_reviews)}개의 리뷰를 크롤링했습니다.',
                'reviews': filtered_reviews,
                'raw_count': len(raw_reviews),
                'filtered_count': len(filtered_reviews)
            })
            
        except Exception as e:
            logger.error(f"[MusinsaCrawler] 오류: {e}")
            result['message'] = f'크롤링 중 오류가 발생했습니다: {str(e)}'
        
        return result

# ===== 편의 함수 (backward compatibility) =====

def crawl_musinsa_reviews(
    product_url: str,
    max_reviews: int = 100,
) -> Dict:
    """
    무신사 리뷰 크롤링 편의 함수
    
    사용 예:
        result = crawl_musinsa_reviews(
            "https://www.musinsa.com/products/3242941",
            max_reviews=100
        )
    """
    crawler = MusinsaCrawler()
    return crawler.crawl_reviews(
        product_url=product_url,
        max_reviews=max_reviews,
    )