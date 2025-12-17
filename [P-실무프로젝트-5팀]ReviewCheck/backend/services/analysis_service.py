"""
분석 서비스 (독립적)
"""
import re
import time
from sqlalchemy.orm import Session
from models.analysis import Analysis
from services.musinsa_api_crawler import MusinsaCrawler
from services.gemini_summarizer import GeminiSummarizer
import logging
import random
import json
import subprocess
import sys
import os
import asyncio

# 🎯 Gemini API 임포트
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("⚠️ google-generativeai 패키지가 설치되지 않았습니다. Gemini 분석 근거 생성을 사용할 수 없습니다.")

logger = logging.getLogger(__name__)

# 🎯 Gemini API 설정
if GEMINI_AVAILABLE:
    try:
        # 환경 변수에서 API 키 읽기
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            gemini_model = genai.GenerativeModel('gemini-2.5-flash-lite')
            logger.info("✅ Gemini API 초기화 완료")
        else:
            GEMINI_AVAILABLE = False
            logger.warning("⚠️ GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. 간단한 템플릿을 사용합니다.")
    except Exception as e:
        GEMINI_AVAILABLE = False
        logger.error(f"❌ Gemini API 초기화 실패: {e}")




# ============================================================
# Gemini API 분석 근거 생성 함수들
# ============================================================

def generate_simple_reason(score: float) -> str:
    """
    Gemini 실패 시 사용할 간단한 템플릿
    """
    if score >= 76:
        return f"AI 분석 결과 {score}%의 높은 신뢰도를 보이는 리뷰입니다."
    elif score >= 36:
        return f"AI 분석 결과 {score}%의 신뢰도를 보이는 리뷰입니다."
    else:
        return f"AI 분석 결과 {score}%의 신뢰도를 보이는 리뷰입니다."


async def generate_reasons_batch(reviews: list) -> list:
    if not GEMINI_AVAILABLE:
        return [generate_simple_reason(r.get('reliability_score', 0)) for r in reviews]

    # 1. 리뷰 데이터 JSON 변환
    review_payload = [
        {
            "index": i,
            "text": r.get("content") or r.get("text", ""),
            "score": r.get("reliability_score", 0),
            "rating": r.get("rating", 0),
        }
        for i, r in enumerate(reviews)
    ]

    prompt = f"""
        다음은 여러 개의 리뷰 데이터입니다. 각 리뷰가 해당 신뢰도 점수를 받은 근거를 생성해주세요.

        규칙:
        1. 인사말, 이모티콘, 감탄사 금지 (예: 안녕하세요, 😊, ! 등)
        2. 불필요한 도입 문장 금지
            - "리뷰는 ~", "이 리뷰는 ~", "사용자는 ~" 같은 표현 없이 바로 핵심 설명 시작
        3. 전문적이면서도 자연스러운 설명체
        4. 2~3문장으로 간결하게
        5. 리뷰의 구체적인 내용(키워드, 길이, 별점과의 일치 여부 등)을 근거로 제시
        6. **과 같은 특수 문자로 강조 금지.
        7. 리뷰 순서를 유지해 결과를 JSON 배열로 출력
        8. 출력 형식:
        [
        {{"index": 0, "reason": "..." }},
        {{"index": 1, "reason": "..." }}
        ]

        아래 리뷰 목록을 분석하여 JSON 배열만 출력하세요.
        설명, 인사말, 코드블록, 문장 등 JSON 외 텍스트는 절대 포함하지 마세요.

        리뷰 목록:
        {json.dumps(review_payload, ensure_ascii=False, indent=2)}
        """

    try:
        # 3. Gemini 요청
        response = await asyncio.to_thread(
            gemini_model.generate_content,
            prompt
        )
        text = response.text.strip()

        # 4. JSON 배열만 추출
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if not match:
            raise ValueError("JSON 배열이 응답에 없음")

        json_array_str = match.group()

        # 5. 파싱
        result_items = json.loads(json_array_str)

        # 6. index 순서대로 reason 정렬
        reasons = [""] * len(reviews)
        for item in result_items:
            idx = item["index"]
            reasons[idx] = item["reason"]

        # 7. 배치 처리 성공 → 최종 결과 return
        return reasons

    except Exception as e:
        logger.error(f"JSON 파싱 실패 → fallback 사용: {e}")

        # 8. fallback: 간단 규칙 기반 설명 반환
        return [
            generate_simple_reason(r.get("reliability_score", 0))
            for r in reviews
        ]

class AnalysisService:
    
    @staticmethod
    def create_analysis(db: Session, review_url: str) -> Analysis:
        analysis = Analysis(review_url=review_url, status='queued')
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis
    
    @staticmethod
    def get_analysis(db: Session, analysis_id: int) -> Analysis:
        return db.query(Analysis).filter(Analysis.analysis_id == analysis_id).first()
    
    @staticmethod
    def list_analyses(db: Session, status: str = None, skip: int = 0, limit: int = 10) -> list:
        query = db.query(Analysis)
        if status: query = query.filter(Analysis.status == status)
        analyses = query.order_by(Analysis.created_at.desc()).offset(skip).limit(limit).all()
        return [analysis.to_dict() for analysis in analyses]
    
    @staticmethod
    def update_analysis_status(db: Session, analysis_id: int, status: str, **kwargs):
        analysis = db.query(Analysis).filter(Analysis.analysis_id == analysis_id).first()
        if analysis:
            analysis.status = status
            for key, value in kwargs.items():
                if hasattr(analysis, key) and value is not None:
                    setattr(analysis, key, value)
            db.commit()
            db.refresh(analysis)
        return analysis
    
    @staticmethod
    async def analyze_with_ai(reviews: list, analysis_id: int, db: Session) -> dict:
        """AI 서버(subprocess) 실행 및 결과 반환"""
        try:
            logger.info(f"[Analysis {analysis_id}] ========================================")
            logger.info(f"[Analysis {analysis_id}] 🤖 2단계 AI 분석 시작 ")
            logger.info(f"[Analysis {analysis_id}] ========================================")
            logger.info(f"[Analysis {analysis_id}] 📊 리뷰 개수: {len(reviews)}개")

            input_data = {'reviews': reviews, 'analysis_id': analysis_id}
            input_json = json.dumps(input_data, ensure_ascii=False)
            
            start_time = time.time()

            my_env = os.environ.copy()
            my_env["PYTHONIOENCODING"] = "utf-8"

            # ai_analyzer.py 실행 (타임아웃 5분)
            process = subprocess.run(
                [sys.executable, 'services/ai_analyzer.py'],
                input=input_json,
                capture_output=True,
                text=True,
                encoding='utf-8', 
                env=my_env,
                timeout=300
            )
            
            if process.stderr:
                logger.info(f"[Analysis {analysis_id}] {'='*50}")
                logger.info(f"[Analysis {analysis_id}] AI 스크립트 상세 로그:")
                for line in process.stderr.split('\n'):
                    if line.strip():
                        logger.info(f"[Analysis {analysis_id}] [AI] {line}")
                logger.info(f"[Analysis {analysis_id}] {'='*50}")
            
            elapsed_time = time.time() - start_time
            logger.info(f"[Analysis {analysis_id}] ⏱️  실행 시간: {elapsed_time:.2f}초")
            
            # 3. 결과 파싱
            if process.returncode != 0:
                logger.error(f"[Analysis {analysis_id}] ❌ AI 스크립트 실행 실패!")
                logger.error(f"[Analysis {analysis_id}] STDERR: {process.stderr}")
                raise Exception(f"AI 스크립트 실행 실패: {process.stderr}")
            
            output_data = json.loads(process.stdout)
            
            if not output_data.get('success'):
                error_msg = output_data.get('error', 'AI 분석 실패')
                raise Exception(error_msg)
            
            ai_result = output_data['result']
            verdict = ai_result.get('verdict')
            confidence = ai_result.get('confidence', 0)
            enriched_reviews = ai_result.get('enriched_reviews', [])  # 🎯 추가!
            
            logger.info(f"[Analysis {analysis_id}] ✅ 2단계 AI 분석 완료: {verdict} ({confidence}%)")
            logger.info(f"[Analysis {analysis_id}] 📝 enriched_reviews: {len(enriched_reviews)}개")
            
            # 🔍 샘플 확인
            if enriched_reviews and len(enriched_reviews) > 0:
                sample = enriched_reviews[0]
                logger.info(f"[Analysis {analysis_id}] 🎯 샘플 신뢰도: {sample.get('reliability_score')}%, "
                           f"label={sample.get('analysis_label')}, color={sample.get('color_class')}")
            
            return {
                'success': True,
                'verdict': verdict,
                'confidence': confidence,
                'enriched_reviews': enriched_reviews,  # 🎯 추가!
                'details': ai_result.get('details', {}),
                'message': '2단계 AI 분석이 완료되었습니다.'
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"[Analysis {analysis_id}] ⏱️  AI 분석 타임아웃")
            AnalysisService.update_analysis_status(
                db, analysis_id, 'failed',
                error_message='AI 분석 시간 초과'
            )
            return {'success': False, 'message': 'AI 분석 시간이 초과되었습니다.'}
            
        except Exception as e:
            logger.error(f"[Analysis {analysis_id}] ❌ AI 분석 오류: {str(e)}")
            AnalysisService.update_analysis_status(
                db, analysis_id, 'failed',
                error_message=f'AI 분석 오류: {str(e)}'
            )
            return {'success': False, 'message': f'AI 분석 중 오류가 발생했습니다: {str(e)}'}

    @staticmethod
    async def process_analysis(analysis_id: int, review_url: str, db: Session):
        """전체 분석 파이프라인"""
        try:
            logger.info(f"[Analysis {analysis_id}] 🚀 분석 시작")
            AnalysisService.update_analysis_status(db, analysis_id, 'processing')
            
            # 1. 크롤링
            crawler = MusinsaCrawler()
            crawl_result = crawler.crawl_reviews(product_url=review_url, max_reviews=500)
            if not crawl_result['success']:
                raise Exception(crawl_result['message'])
            
            raw_reviews = crawl_result['reviews']
            logger.info(f"크롤링 완료: {len(raw_reviews)}개")

            # 2. AI 분석 실행
            ai_result = await AnalysisService.analyze_with_ai(raw_reviews, analysis_id, db)
            
            # 점수가 포함된 리뷰 리스트 가져오기 (없으면 원본)
            enriched_reviews = ai_result.get('enriched_reviews', raw_reviews)

            # 3. 데이터 포맷 통일 및 상위/하위 추출
            def normalize(r):
                """프론트엔드 호환 포맷 변환"""
                return {
                    "content": r.get('text') or r.get('content', ''),
                    "rating": int(r.get('rating', 0)),
                    "date": r.get('date', ''),
                    "author": r.get('author', '***'),
                    # AI 분석 결과 필드 (중요!)
                    "reliability_score": r.get('reliability_score', 0),
                    "analysis_label": r.get('analysis_label', '분석 대기'),
                    "color_class": r.get('color_class', 'status-gray'),
                    "analysis_reason": r.get('analysis_reason', 'AI 분석 결과를 기다리는 중입니다.')  # 🎯 추가
                }

            # 평점 기준 분리
            high_rated = [r for r in enriched_reviews if r.get('rating', 0) >= 4]
            low_rated = [r for r in enriched_reviews if r.get('rating', 0) <= 3]
            
            # 랜덤 섞기
            random.shuffle(high_rated)
            random.shuffle(low_rated)
            
            # 상위 10개, 하위 10개 선택
            top_10_raw = high_rated[:10]
            worst_10_raw = low_rated[:10]
            
            # 🎯 Gemini로 20개 리뷰의 분석 근거 생성
            special_reviews = top_10_raw + worst_10_raw
            
            if special_reviews:
                logger.info(f"🌟 Gemini API로 {len(special_reviews)}개 리뷰 분석 근거 생성 시작...")
                try:
                    reasons = await generate_reasons_batch(special_reviews)
                    
                    # 생성된 근거를 각 리뷰에 추가
                    for i, review in enumerate(special_reviews):
                        review['analysis_reason'] = reasons[i]
                    
                    logger.info(f"✅ Gemini 분석 근거 생성 완료")
                    
                except Exception as e:
                    logger.error(f"❌ Gemini 배치 처리 실패: {e}")
                    # Fallback: 간단한 템플릿
                    for review in special_reviews:
                        review['analysis_reason'] = generate_simple_reason(
                            review.get('reliability_score', 0)
                        )
            
            # Normalize
            top_reviews = [normalize(r) for r in top_10_raw]
            worst_reviews = [normalize(r) for r in worst_10_raw]

            # 4. 평균 별점 계산 (크롤링 데이터에서 직접)
            avg_rating = 0
            try:
                # rating 필드가 있는 리뷰들만 추출
                valid_ratings = [r.get('rating') for r in raw_reviews if r.get('rating') is not None]
                if valid_ratings:
                    avg_rating = round(sum(valid_ratings) / len(valid_ratings), 1)
                    logger.info(f"평균 별점: {avg_rating} ({len(valid_ratings)}개 리뷰 기준)")
            except Exception as e:
                logger.error(f"평균 별점 계산 실패: {e}")

            # 5. Gemini 요약
            gemini_summary = ""
            try:
                summarizer = GeminiSummarizer()
                gemini_summary = summarizer.summarize_reviews(raw_reviews, max_reviews=50)
            except Exception as e:
                logger.error(f"Gemini 요약 실패: {e}")

            # 6. DB 저장
            AnalysisService.update_analysis_status(
                db, analysis_id, 'completed',
                verdict=ai_result.get('verdict'),
                confidence=ai_result.get('confidence'),
                review_count=len(raw_reviews),
                top_reviews=top_reviews,      
                worst_reviews=worst_reviews,
                summary=gemini_summary,
                avg_rating=avg_rating
            )
            logger.info(f"[Analysis {analysis_id}] ✅ 분석 완료")

        except Exception as e:
            logger.error(f"파이프라인 오류: {e}")
            AnalysisService.update_analysis_status(db, analysis_id, 'failed', error_message=str(e))