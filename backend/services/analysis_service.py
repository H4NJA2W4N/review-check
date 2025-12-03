"""
분석 서비스 (독립적)
리뷰 분석 전담 (크롤링은 MusinsaCrawler에 위임)
"""
from sqlalchemy.orm import Session
from models.analysis import Analysis
from services.musinsa_api_crawler import MusinsaCrawler
import logging

logger = logging.getLogger(__name__)


class AnalysisService:
    """분석 서비스"""
    
    @staticmethod
    def create_analysis(db: Session, review_url: str) -> Analysis:
        """
        분석 요청 생성
        
        Args:
            db: 데이터베이스 세션
            review_url: 분석할 무신사 상품 URL
        
        Returns:
            생성된 Analysis 객체
        """
        analysis = Analysis(
            review_url=review_url,
            status='queued'
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis
    
    @staticmethod
    def get_analysis(db: Session, analysis_id: int) -> Analysis:
        """분석 요청 조회"""
        return db.query(Analysis).filter(Analysis.analysis_id == analysis_id).first()
    
    @staticmethod
    def list_analyses(
        db: Session,
        status: str = None,
        skip: int = 0,
        limit: int = 10
    ) -> list:
        """분석 목록 조회"""
        query = db.query(Analysis)
        
        if status:
            query = query.filter(Analysis.status == status)
        
        analyses = query.order_by(Analysis.created_at.desc()).offset(skip).limit(limit).all()
        return [analysis.to_dict() for analysis in analyses]
    
    @staticmethod
    def update_analysis_status(
        db: Session, 
        analysis_id: int, 
        status: str,
        verdict: str = None,
        confidence: float = None,
        error_message: str = None,
        review_count: int = None
    ):
        """분석 상태 업데이트"""
        analysis = db.query(Analysis).filter(Analysis.analysis_id == analysis_id).first()
        if analysis:
            analysis.status = status
            if verdict:
                analysis.verdict = verdict
            if confidence is not None:
                analysis.confidence = confidence
            if error_message:
                analysis.error_message = error_message
            if review_count is not None:
                analysis.review_count = review_count
            db.commit()
            db.refresh(analysis)
        return analysis
    
    @staticmethod
    async def analyze_with_ai(reviews: list, analysis_id: int, db: Session) -> dict:
        """
        AI 서버로 리뷰 분석 요청
        
        웹서버에서 AI Python 스크립트를 실행합니다.
        
        Args:
            reviews: 필터링된 리뷰 리스트
            analysis_id: 분석 ID
            db: 데이터베이스 세션
        
        Returns:
            분석 결과
        """
        try:
            logger.info(f"[Analysis {analysis_id}] ========================================")
            logger.info(f"[Analysis {analysis_id}] 🤖 AI 분석 시작")
            logger.info(f"[Analysis {analysis_id}] ========================================")
            logger.info(f"[Analysis {analysis_id}] 📊 리뷰 개수: {len(reviews)}개")
            
            # === AI 스크립트 실행 (subprocess) ===
            import subprocess
            import json
            
            # 1. 입력 데이터 준비
            logger.info(f"[Analysis {analysis_id}] 📝 Step 1: 입력 데이터 준비")
            input_data = {
                'reviews': reviews,
                'analysis_id': analysis_id
            }
            input_json = json.dumps(input_data, ensure_ascii=False)
            logger.info(f"[Analysis {analysis_id}] ✅ 입력 데이터 크기: {len(input_json)} bytes")
            
            # 샘플 리뷰 출력
            if reviews:
                logger.info(f"[Analysis {analysis_id}] 📄 첫 번째 리뷰 샘플: {reviews[0].get('text', '')[:50]}...")
            
            # 2. AI 스크립트 실행
            logger.info(f"[Analysis {analysis_id}] 🚀 Step 2: AI 스크립트 실행 중...")
            logger.info(f"[Analysis {analysis_id}] 명령: python services/ai_analyzer.py")
            
            import time
            start_time = time.time()
            
            process = subprocess.run(
                ['python', 'services/ai_analyzer.py'],
                input=input_json,
                capture_output=True,
                text=True,
                timeout=120,  # 최대 2분
                bufsize=1
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"[Analysis {analysis_id}] ⏱️  실행 시간: {elapsed_time:.2f}초")
            
            # 3. subprocess 결과 로깅
            logger.info(f"[Analysis {analysis_id}] 📋 Step 3: AI 스크립트 출력 확인")
            logger.info(f"[Analysis {analysis_id}] Return Code: {process.returncode}")
            
            if process.stdout:
                logger.info(f"[Analysis {analysis_id}] ===== AI 스크립트 STDOUT =====")
                for line in process.stdout.split('\n')[:20]:  # 최대 20줄
                    if line.strip():
                        logger.info(f"[Analysis {analysis_id}] {line}")
                logger.info(f"[Analysis {analysis_id}] ================================")
            
            if process.stderr:
                logger.warning(f"[Analysis {analysis_id}] ===== AI 스크립트 STDERR =====")
                for line in process.stderr.split('\n')[:20]:  # 최대 20줄
                    if line.strip():
                        logger.warning(f"[Analysis {analysis_id}] {line}")
                logger.warning(f"[Analysis {analysis_id}] ================================")
            
            # 4. 결과 파싱
            if process.returncode != 0:
                logger.error(f"[Analysis {analysis_id}] ❌ AI 스크립트 실행 실패!")
                logger.error(f"[Analysis {analysis_id}] 에러: {process.stderr}")
                raise Exception(f"AI 스크립트 실행 실패: {process.stderr}")
            
            logger.info(f"[Analysis {analysis_id}] 🔍 Step 4: JSON 파싱")
            output_data = json.loads(process.stdout)
            logger.info(f"[Analysis {analysis_id}] ✅ JSON 파싱 성공")
            
            if not output_data.get('success'):
                error_msg = output_data.get('error', 'AI 분석 실패')
                logger.error(f"[Analysis {analysis_id}] ❌ AI 분석 실패: {error_msg}")
                raise Exception(error_msg)
            
            ai_result = output_data['result']
            
            # 5. 결과 추출
            logger.info(f"[Analysis {analysis_id}] 📊 Step 5: 결과 추출")
            verdict = ai_result.get('verdict')
            confidence = ai_result.get('confidence', 0)
            details = ai_result.get('details', {})
            
            logger.info(f"[Analysis {analysis_id}] ========================================")
            logger.info(f"[Analysis {analysis_id}] 🎯 AI 분석 결과")
            logger.info(f"[Analysis {analysis_id}] ========================================")
            logger.info(f"[Analysis {analysis_id}] 판정: {verdict}")
            logger.info(f"[Analysis {analysis_id}] 신뢰도: {confidence}%")
            
            if details:
                logger.info(f"[Analysis {analysis_id}] 세부 정보:")
                for key, value in details.items():
                    logger.info(f"[Analysis {analysis_id}]   - {key}: {value}")
            
            result = {
                'success': True,
                'verdict': verdict,
                'confidence': confidence,
                'details': details,
                'message': 'AI 분석이 완료되었습니다.'
            }
            
            # 6. 분석 완료 상태로 업데이트
            logger.info(f"[Analysis {analysis_id}] 💾 Step 6: DB 업데이트")
            AnalysisService.update_analysis_status(
                db, analysis_id, 'completed',
                verdict=result['verdict'],
                confidence=result['confidence'],
                review_count=len(reviews)
            )
            
            logger.info(f"[Analysis {analysis_id}] ========================================")
            logger.info(f"[Analysis {analysis_id}] ✅ AI 분석 완료!")
            logger.info(f"[Analysis {analysis_id}] ========================================")
            
            return result
            
        except subprocess.TimeoutExpired:
            logger.error(f"[Analysis {analysis_id}] ========================================")
            logger.error(f"[Analysis {analysis_id}] ⏱️  AI 분석 타임아웃 (2분 초과)")
            logger.error(f"[Analysis {analysis_id}] ========================================")
            AnalysisService.update_analysis_status(
                db, analysis_id, 'failed',
                error_message='AI 분석 시간 초과 (2분)'
            )
            return {
                'success': False,
                'message': 'AI 분석 시간이 초과되었습니다.'
            }
            
        except Exception as e:
            logger.error(f"[Analysis {analysis_id}] ========================================")
            logger.error(f"[Analysis {analysis_id}] ❌ AI 분석 오류")
            logger.error(f"[Analysis {analysis_id}] ========================================")
            logger.error(f"[Analysis {analysis_id}] 에러 메시지: {str(e)}")
            
            import traceback
            logger.error(f"[Analysis {analysis_id}] 스택 트레이스:")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    logger.error(f"[Analysis {analysis_id}] {line}")
            
            AnalysisService.update_analysis_status(
                db, analysis_id, 'failed',
                error_message=f'AI 분석 오류: {str(e)}'
            )
            return {
                'success': False,
                'message': f'AI 분석 중 오류가 발생했습니다: {str(e)}'
            }
    
    @staticmethod
    async def process_analysis(analysis_id: int, review_url: str, db: Session) -> dict:
        """
        전체 분석 파이프라인 실행
        
        1. 리뷰 크롤링 (CrawlingService에 위임)
        2. AI 분석
        3. 결과 저장
        
        Args:
            analysis_id: 분석 ID
            review_url: 무신사 상품 URL
            db: 데이터베이스 세션
        
        Returns:
            최종 분석 결과
        """
        try:
            logger.info(f"")
            logger.info(f"{'='*70}")
            logger.info(f"[Analysis {analysis_id}] 🚀 분석 파이프라인 시작")
            logger.info(f"{'='*70}")
            logger.info(f"[Analysis {analysis_id}] URL: {review_url}")
            
            # 1. 상태 업데이트: processing
            logger.info(f"[Analysis {analysis_id}] 📝 상태: queued → processing")
            AnalysisService.update_analysis_status(db, analysis_id, 'processing')
            
            # 2. 크롤링 (MusinsaCrawler에 위임)
            logger.info(f"")
            logger.info(f"[Analysis {analysis_id}] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.info(f"[Analysis {analysis_id}] 🕷️  Step 1/3: 리뷰 크롤링")
            logger.info(f"[Analysis {analysis_id}] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            import time
            crawl_start = time.time()
            
            crawler = MusinsaCrawler()
            crawl_result = crawler.crawl_reviews(
                product_url=review_url,
                max_reviews=100,  # 설정 가능
                #save_to_db=True,  # DB에 저장
                #db=db
            )
            
            crawl_time = time.time() - crawl_start
            
            if not crawl_result['success']:
                logger.error(f"[Analysis {analysis_id}] ❌ 크롤링 실패: {crawl_result['message']}")
                AnalysisService.update_analysis_status(
                    db, analysis_id, 'failed',
                    error_message=crawl_result['message']
                )
                return {
                    'success': False,
                    'message': crawl_result['message'],
                    'analysis_id': analysis_id,
                    'status': 'failed'
                }
            
            logger.info(f"[Analysis {analysis_id}] ✅ 크롤링 완료!")
            logger.info(f"[Analysis {analysis_id}] ⏱️  소요 시간: {crawl_time:.2f}초")
            logger.info(f"[Analysis {analysis_id}] 📊 수집된 리뷰: {crawl_result['raw_count']}개")
            logger.info(f"[Analysis {analysis_id}] 🎯 필터링된 리뷰: {crawl_result['filtered_count']}개")
            
            if crawl_result['filtered_count'] == 0:
                logger.warning(f"[Analysis {analysis_id}] ⚠️  분석할 리뷰가 없습니다")
                AnalysisService.update_analysis_status(
                    db, analysis_id, 'failed',
                    error_message='분석할 리뷰가 없습니다'
                )
                return {
                    'success': False,
                    'message': '분석할 리뷰가 없습니다',
                    'analysis_id': analysis_id,
                    'status': 'failed'
                }
            
            # 3. AI 분석
            logger.info(f"")
            logger.info(f"[Analysis {analysis_id}] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.info(f"[Analysis {analysis_id}] 🤖 Step 2/3: AI 분석")
            logger.info(f"[Analysis {analysis_id}] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            ai_start = time.time()
            
            ai_result = await AnalysisService.analyze_with_ai(
                reviews=crawl_result['reviews'],
                analysis_id=analysis_id,
                db=db
            )
            
            ai_time = time.time() - ai_start
            logger.info(f"[Analysis {analysis_id}] ⏱️  AI 분석 소요 시간: {ai_time:.2f}초")
            
            if not ai_result['success']:
                logger.error(f"[Analysis {analysis_id}] ❌ AI 분석 실패")
                return {
                    'success': False,
                    'message': ai_result['message'],
                    'analysis_id': analysis_id,
                    'status': 'failed'
                }
            
            # 4. 최종 결과 반환
            logger.info(f"")
            logger.info(f"[Analysis {analysis_id}] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.info(f"[Analysis {analysis_id}] 💾 Step 3/3: 결과 저장 및 완료")
            logger.info(f"[Analysis {analysis_id}] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            analysis = AnalysisService.get_analysis(db, analysis_id)
            
            total_time = crawl_time + ai_time
            
            logger.info(f"")
            logger.info(f"{'='*70}")
            logger.info(f"[Analysis {analysis_id}] 🎉 분석 파이프라인 완료!")
            logger.info(f"{'='*70}")
            logger.info(f"[Analysis {analysis_id}] 📊 최종 결과:")
            logger.info(f"[Analysis {analysis_id}]   - 판정: {analysis.verdict}")
            logger.info(f"[Analysis {analysis_id}]   - 신뢰도: {analysis.confidence}%")
            logger.info(f"[Analysis {analysis_id}]   - 리뷰 수: {analysis.review_count}개")
            logger.info(f"[Analysis {analysis_id}]   - 총 소요 시간: {total_time:.2f}초")
            logger.info(f"{'='*70}")
            logger.info(f"")
            
            return {
                'success': True,
                'message': '분석이 완료되었습니다.',
                'analysis_id': analysis.analysis_id,
                'status': analysis.status,
                'verdict': analysis.verdict,
                'confidence': float(analysis.confidence) if analysis.confidence else None,
                'review_count': analysis.review_count
            }
            
        except Exception as e:
            logger.error(f"")
            logger.error(f"{'='*70}")
            logger.error(f"[Analysis {analysis_id}] ❌ 분석 파이프라인 오류")
            logger.error(f"{'='*70}")
            logger.error(f"[Analysis {analysis_id}] 에러: {str(e)}")
            
            import traceback
            logger.error(f"[Analysis {analysis_id}] 스택 트레이스:")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    logger.error(f"[Analysis {analysis_id}] {line}")
            logger.error(f"{'='*70}")
            logger.error(f"")
            
            AnalysisService.update_analysis_status(
                db, analysis_id, 'failed',
                error_message=str(e)
            )
            return {
                'success': False,
                'message': f'분석 처리 중 오류가 발생했습니다: {str(e)}',
                'analysis_id': analysis_id,
                'status': 'failed'
            }