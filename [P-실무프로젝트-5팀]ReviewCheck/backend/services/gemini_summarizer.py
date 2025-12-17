"""
Gemini API를 사용한 리뷰 요약 서비스
"""
import os
import logging
import google.generativeai as genai
from typing import List, Dict

logger = logging.getLogger(__name__)

# Gemini API 키 (환경변수에서 가져오기)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class GeminiSummarizer:
    """Gemini API를 사용한 리뷰 요약기"""
    
    def __init__(self):
        """초기화"""
        self.model = None
        self._configure_api()
    
    def _configure_api(self):
        """Gemini API 설정"""
        if not GEMINI_API_KEY:
            logger.warning("⚠️ GEMINI_API_KEY가 설정되지 않았습니다. 요약 기능이 제한됩니다.")
            return
        
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("✅ Gemini API 설정 완료")
        except Exception as e:
            logger.error(f"❌ Gemini API 설정 실패: {e}")
    
    def summarize_reviews(
        self, 
        reviews: List[Dict], 
        max_reviews: int = 200,
        language: str = "Korean"
    ) -> str:
        """
        리뷰 목록을 요약
        
        Args:
            reviews: 리뷰 리스트 [{"text": "...", "rating": 5}, ...]
            max_reviews: 요약에 사용할 최대 리뷰 수 (토큰 제한 고려)
            language: 요약 언어
        
        Returns:
            요약 텍스트
        """
        
        # # API가 설정되지 않은 경우 기본 요약 반환
        if not self.model:
            return self._generate_basic_summary(reviews)
        
        try:
            # 1. 리뷰 샘플링 (너무 많으면 토큰 초과)
            sampled_reviews = self._sample_reviews(reviews, max_reviews)
            
            # 2. 프롬프트 생성
            prompt = self._create_summary_prompt(sampled_reviews, language)
            
            # 3. Gemini API 호출
            logger.info(f"🤖 Gemini API 요약 시작 (리뷰 {len(sampled_reviews)}개)")
            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            
            logger.info(f"✅ Gemini 요약 완료 ({len(summary)}자)")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Gemini 요약 실패: {e}")
            # 실패 시 기본 요약 반환
            return self._generate_basic_summary(reviews)
    
    def _sample_reviews(self, reviews: List[Dict], max_count: int) -> List[Dict]:
        """
        리뷰 샘플링 (다양한 평점 고려)
        
        Args:
            reviews: 전체 리뷰 리스트
            max_count: 최대 샘플 수
        
        Returns:
            샘플링된 리뷰 리스트
        """
        if len(reviews) <= max_count:
            return reviews
        
        # 평점별로 분류
        high_rated = [r for r in reviews if r.get('rating', 0) >= 4]
        mid_rated = [r for r in reviews if 2 < r.get('rating', 0) < 4]
        low_rated = [r for r in reviews if r.get('rating', 0) <= 2]
        
        # 비율대로 샘플링
        high_count = min(len(high_rated), int(max_count * 0.5))
        mid_count = min(len(mid_rated), int(max_count * 0.3))
        low_count = min(len(low_rated), int(max_count * 0.2))
        
        # 부족한 경우 나머지로 채우기
        remaining = max_count - (high_count + mid_count + low_count)
        if remaining > 0:
            high_count += remaining
        
        import random
        sampled = []
        if high_rated:
            sampled.extend(random.sample(high_rated, min(high_count, len(high_rated))))
        if mid_rated:
            sampled.extend(random.sample(mid_rated, min(mid_count, len(mid_rated))))
        if low_rated:
            sampled.extend(random.sample(low_rated, min(low_count, len(low_rated))))
        
        return sampled
    
    def _create_summary_prompt(self, reviews: List[Dict], language: str) -> str:
        """
        Gemini API용 프롬프트 생성
        
        Args:
            reviews: 리뷰 리스트
            language: 요약 언어
        
        Returns:
            프롬프트 문자열
        """
        
        # 리뷰 텍스트 포맷팅
        review_texts = []
        for idx, review in enumerate(reviews, 1):
            text = review.get('text', '')
            rating = review.get('rating', 0)
            review_texts.append(f"{idx}. [별점 {rating}점] {text}")
        
        reviews_str = "\n".join(review_texts)
        
        prompt = f"""
            당신은 상품 리뷰를 객관적이고 자연스럽게 요약하는 전문가입니다.
            아래 리뷰들을 분석하여 **사용자에게 자연스럽게 읽히는 요약문**을 작성하세요.

            **리뷰 데이터 ({len(reviews)}개):**
            {reviews_str}

            **요약 작성 기준:**
            1. 전체적인 평가 경향을 담되, **중립적이고 절제된 표현**을 사용하세요.
            2. 자주 언급되는 장점과 단점을 **구체적으로 1~2개씩** 정리하세요.
            3. **사실 기반**으로 작성하고, 추측이나 과장(예: '인생 슬랙스', '극찬', '최고')을 피하세요.
            4. 광고 문구나 감탄사는 쓰지 마세요.
            5. 불필요하게 화려한 표현 대신, **실제 사용자가 느낄 법한 자연스러운 문장**을 작성하세요.
            6. 요약은 2~3문장으로 간결하게 작성하세요.
            7. 결과는 {language}로 작성하세요.

            **금지 표현 예시:**
            - 인생 OO, 최고의 OO, 완벽한, 극찬, 압도적, 감탄스러운 등 과장 표현
            - 단정적 표현(“반드시 ~해야 함”) 
            - 사용자 발화를 그대로 복붙하는 표현

            요약:
        """
        
        return prompt
    
    def _generate_basic_summary(self, reviews: List[Dict]) -> str:
        """
        Gemini API 없이 기본적인 요약 생성
        
        Args:
            reviews: 리뷰 리스트
        
        Returns:
            기본 요약 텍스트
        """
        if not reviews:
            return "분석할 리뷰가 없습니다."
        
        # 통계 계산
        total_count = len(reviews)
        avg_rating = sum(r.get('rating', 0) for r in reviews) / total_count if total_count > 0 else 0
        
        high_rated = len([r for r in reviews if r.get('rating', 0) >= 4])
        low_rated = len([r for r in reviews if r.get('rating', 0) <= 2])
        
        # 기본 요약 생성
        summary = f"총 {total_count}개의 리뷰가 수집되었습니다. "
        summary += f"평균 평점은 {avg_rating:.1f}점입니다. "
        
        if high_rated > total_count * 0.7:
            summary += "대부분의 사용자들이 긍정적으로 평가하고 있습니다."
        elif low_rated > total_count * 0.3:
            summary += "일부 사용자들이 부정적인 의견을 표현했습니다."
        else:
            summary += "다양한 의견이 존재합니다."
        
        return summary


# ===== 편의 함수 =====

def summarize_reviews(reviews: List[Dict], **kwargs) -> str:
    """
    리뷰 요약 편의 함수
    
    사용 예:
        summary = summarize_reviews(reviews, max_reviews=200)
    """
    summarizer = GeminiSummarizer()
    return summarizer.summarize_reviews(reviews, **kwargs)