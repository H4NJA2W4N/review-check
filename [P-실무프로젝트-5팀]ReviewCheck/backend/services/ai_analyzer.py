"""
AI 리뷰 분석기 (독립 실행)
입력: JSON (stdin 또는 파일)
출력: JSON (stdout)
"""
import re
import sys
import json
import argparse
import os
from pathlib import Path
import logging
import io
from review_scorer import SmartReviewScorer

# 한글 인코딩 설정
sys.stderr.flush()
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

class ReviewAIAnalyzer:
    """리뷰 AI 분석기 (SmartReviewScorer 사용)"""
    
    def __init__(self, model_path="final_perfect_scorer.pkl", use_retrained=True):
        # 프로젝트 루트 경로 계산
        current_file = Path(__file__).resolve()
        
        # services/ai_analyzer.py -> backend/ 경로
        if current_file.parent.name == 'services':
            backend_root = current_file.parent.parent  # services -> backend
        else:
            backend_root = current_file.parent  # 직접 backend에 있는 경우
        # backend → project_root
        project_root = backend_root.parent
        # RandomForest 모델 경로 (절대 경로로 변환)
        if os.path.isabs(model_path):
            self.rf_model_path = model_path
        else:
            # 상대 경로면 backend 기준으로 변환
            # 예: "final_perfect_scorer.pkl" -> "backend/ai_models/final_perfect_scorer.pkl"
            # 예: "ai_models/final_perfect_scorer.pkl" -> "backend/ai_models/final_perfect_scorer.pkl"
            if not model_path.startswith('ai_models'):
                model_path = f"ai_models/{model_path}"
            self.rf_model_path = project_root / model_path
        
        self.use_retrained = use_retrained
        self.scorer = None
        
        logger.info(f"="*60)
        logger.info(f"AI 분석기 초기화")
        logger.info(f"  KcELECTRA: beomi/KcELECTRA-base (고정)")
        logger.info(f"  RandomForest 기본 경로: {self.rf_model_path}")
        logger.info(f"  재학습 모델 사용: {use_retrained}")
        logger.info(f"="*60)

    def load_model(self):
        """SmartReviewScorer 로드"""
        try:
            logger.info("="*60)
            logger.info("SmartReviewScorer 로딩 시작...")
            logger.info("="*60)
            
            # ✅ 새로운 방식: use_retrained 파라미터 사용
            self.scorer = SmartReviewScorer(
                model_path=str(self.rf_model_path),
                use_retrained=self.use_retrained
            )
            
            logger.info("="*60)
            logger.info("✅ SmartReviewScorer 로딩 완료")
            logger.info(f"   - 디바이스: {self.scorer.device}")
            logger.info(f"   - KcELECTRA: {self.scorer.model_name}")
            logger.info(f"   - RandomForest 모델 로드됨")
            logger.info("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ SmartReviewScorer 로딩 실패: {e}")
            import traceback
            traceback.print_exc()
            return False

    def preprocess_reviews(self, reviews):
        """전처리: 텍스트가 있는 리뷰만 추출"""
        processed = []
        for review in reviews:
            # text나 content 키가 섞여있을 수 있으므로 둘 다 확인
            text = review.get('text', '') or review.get('content', '')
            if not text:
                continue
            
            # 원본 데이터 보존하며 text 필드 통일
            item = review.copy()
            item['text'] = text.strip()
            processed.append(item)
        
        logger.info(f"📊 전처리 완료: {len(processed)}개 리뷰")
        return processed
    
    def analyze_reviews(self, reviews):
        """리뷰 분석 수행 및 개별 점수 마킹"""
        try:
            logger.info("="*60)
            logger.info(f"AI 분석 시작: {len(reviews)}개 리뷰")
            logger.info("="*60)
            
            # ========================================
            # SmartReviewScorer로 개별 리뷰 점수 계산
            # ========================================
            logger.info("[Step 1] SmartReviewScorer 분석 중...")
            
            final_scores = []
            for review in reviews:
                text = review['text']
                score = self.scorer.predict(text)  # text만 전달
                final_scores.append(score)
            
            logger.info(f"✅ {len(final_scores)}개 리뷰 분석 완료")

            # ========================================
            # Step 2: 개별 리뷰에 점수 및 라벨/색상 부착
            # ========================================
            enriched_reviews = []
            for i, review in enumerate(reviews):
                score = final_scores[i]

                # 라벨링 및 색상 결정
                if score >= 76:
                    label = "매우 도움됨"
                    color = "status-green"
                elif score >= 36:
                    label = "부분적으로 도움됨"
                    color = "status-orange"
                else:
                    label = "도움 안됨"
                    color = "status-red"

                # 리뷰 데이터에 점수 및 라벨 추가
                review["reliability_score"] = score
                review["analysis_label"] = label
                review["color_class"] = color

                enriched_reviews.append(review)
            
            # ========================================
            # Step 3: 전체 통계 및 판정
            # ========================================
            avg_score = sum(final_scores) / len(final_scores) if final_scores else 0
            avg_trust = avg_score / 100  # 0-1 범위로 정규화
            
            # 전체 판정
            if avg_trust > 0.7:
                verdict = 'safe'
                verdict_kr = '신뢰할 만함'
            elif avg_trust >= 0.3:
                verdict = 'suspicious'
                verdict_kr = '의심스러움'
            else:
                verdict = 'malicious'
                verdict_kr = '신뢰하기 어려움'

            confidence = round(avg_score, 2)
            
            result = {
                'verdict': verdict,
                'verdict_kr': verdict_kr,
                'confidence': confidence,
                'enriched_reviews': enriched_reviews,
                'details': {
                    'avg_trust_score': round(avg_trust, 4),
                    'avg_score': round(avg_score, 2),
                    'total_reviews': len(reviews),
                    'model_mode': 'SmartReviewScorer (KcELECTRA + RandomForest)'
                }
            }
            
            logger.info("="*60)
            logger.info(f"✅ AI 분석 완료")
            logger.info(f"   - 판정: {verdict_kr}")
            logger.info(f"   - 평균 점수: {avg_score:.1f}점")
            logger.info(f"   - 신뢰도: {confidence}%")
            logger.info("="*60)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 분석 실패: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def run(self, reviews):
        if self.scorer is None:
            if not self.load_model():
                return {'verdict': 'error', 'confidence': 0, 'error': '모델 로딩 실패'}
        
        processed_reviews = self.preprocess_reviews(reviews)
        if not processed_reviews:
            return {'verdict': 'error', 'confidence': 0, 'error': '분석할 리뷰 없음'}
            
        return self.analyze_reviews(processed_reviews)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str)
    parser.add_argument('--output', type=str)
    parser.add_argument('--model', type=str, default='final_perfect_scorer.pkl')
    parser.add_argument('--use-retrained', action='store_true', default=True, help='재학습 모델 사용 여부')
    args = parser.parse_args()
    
    try:
        if args.input:
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = json.load(sys.stdin)
        
        reviews = data.get('reviews', [])
        
        analyzer = ReviewAIAnalyzer(
            model_path=args.model,
            use_retrained=args.use_retrained
        )
        result = analyzer.run(reviews)
        
        output_data = {'success': True, 'result': result}
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
        else:
            print(json.dumps(output_data, ensure_ascii=False))
            
    except Exception as e:
        error_data = {'success': False, 'error': str(e)}
        print(json.dumps(error_data, ensure_ascii=False))

if __name__ == "__main__":
    main()