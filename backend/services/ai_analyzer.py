"""
AI 리뷰 분석기 (독립 실행)

웹서버에서 subprocess로 실행됩니다.
입력: JSON (stdin 또는 파일)
출력: JSON (stdout)

사용법:
    python ai_analyzer.py < reviews.json
    또는
    python ai_analyzer.py --input reviews.json --output result.json
"""
import sys
import json
import argparse
from pathlib import Path
import logging
import os

# 🔥 subprocess에서 실행되므로 자체 로깅 설정 필요!
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
sys.stderr.flush()

logger = logging.getLogger(__name__)


class ReviewAIAnalyzer:
    """리뷰 AI 분석기 (KcELECTRA 기반)"""
    
    def __init__(self, model_path="ai_models"):
        """
        AI 모델 초기화
        
        Args:
            model_path: 모델 파일들이 있는 디렉토리 (project/ai_models)
        """

        # 현재 파일(ai_analyzer.py)의 절대 경로
        current_file = Path(__file__).resolve()

        # project/backend/services → project/backend → project/
        project_root = current_file.parent.parent.parent

        # 모델 폴더 절대경로 구성
        self.model_path = project_root / model_path

        # 디버그 출력
        print(f"[AI_ANALYZER] BASE FILE: {current_file}", file=sys.stderr)
        print(f"[AI_ANALYZER] PROJECT ROOT: {project_root}", file=sys.stderr)
        print(f"[AI_ANALYZER] MODEL PATH: {self.model_path}", file=sys.stderr)

        self.model = None
        self.tokenizer = None
        self.device = None
        
        logger.info(f"AI 분석기 초기화: {model_path}")

    def load_model(self):
        """
        AI 모델 로드 (KcELECTRA)
        
        모델 정보:
        - 베이스: beomi/KcELECTRA-base-v2022
        - 클래스: 0=비신뢰, 1=신뢰
        - max_length: 128
        """
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            logger.info("AI 모델 로딩 중...")
            # 1. 디바이스 설정
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"디바이스: {self.device}")
        
            # 2. 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                local_files_only=True
            )
            
            # 3. 모델 로드
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(self.model_path),
                local_files_only=True
            )
            
            # 4. 모델을 디바이스로 이동
            self.model.to(self.device)
            
            # 5. 평가 모드 설정
            self.model.eval()
            
            logger.info("✅ AI 모델 로딩 완료")
            logger.info(f"   - 모델: KcELECTRA")
            logger.info(f"   - 클래스: 2개 (0=비신뢰, 1=신뢰)")
            logger.info(f"   - 디바이스: {self.device}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 모델 로딩 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def preprocess_reviews(self, reviews):
        """
        리뷰 데이터 전처리
        
        Args:
            reviews: 리뷰 리스트 [{"text": "...", "rating": 5}, ...]
        
        Returns:
            전처리된 데이터
        """
        processed = []
        
        for review in reviews:
            text = review.get('text', '')
            rating = review.get('rating', 0)
            
            # 텍스트 정제
            text = text.strip()
            
            if text:
                processed.append({
                    'text': text,
                    'rating': rating,
                    'length': len(text)
                })
        
        logger.info(f"전처리 완료: {len(processed)}개 리뷰")
        return processed
    
    def analyze_reviews(self, reviews):
        """
        리뷰 분석 수행 (실제 AI 모델 사용)
        
        Args:
            reviews: 전처리된 리뷰 리스트
        
        Returns:
            분석 결과 {
                'verdict': 'safe' | 'suspicious' | 'malicious',
                'confidence': float (0-100),
                'details': {...}
            }
        """
        try:
            import torch
            import torch.nn.functional as F
            
            logger.info(f"AI 분석 시작: {len(reviews)}개 리뷰")
            
            # 1. 텍스트 추출
            texts = [r['text'] for r in reviews]
            
            # 2. 배치 처리 (메모리 효율)
            batch_size = 32
            all_trust_scores = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                
                # 토크나이징 (max_length=128)
                inputs = self.tokenizer(
                    batch_texts,
                    return_tensors="pt",
                    truncation=True,
                    max_length=128,  # ← AI 파트 확인됨
                    padding=True
                ).to(self.device)
                
                # 추론
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    
                    # Softmax로 확률 계산
                    probs = F.softmax(outputs.logits, dim=-1)
                    
                    # 클래스 1 (신뢰) 확률 추출
                    trust_probs = probs[:, 1].cpu().tolist()
                    all_trust_scores.extend(trust_probs)
                
                logger.debug(f"배치 {i//batch_size + 1}: {len(batch_texts)}개 처리")
            
            # 3. 결과 집계
            avg_trust = sum(all_trust_scores) / len(all_trust_scores)
            max_trust = max(all_trust_scores)
            min_trust = min(all_trust_scores)
            
            # 4. 판정 (평균 신뢰도 기반)
            # avg_trust > 0.7 → safe (신뢰도 높음)
            # 0.3 <= avg_trust <= 0.7 → suspicious (의심스러움)
            # avg_trust < 0.3 → malicious (신뢰도 낮음, 조작 가능성)
            
            if avg_trust > 0.7:
                verdict = 'safe'
                confidence = avg_trust * 100  # 70~100%
            elif avg_trust >= 0.3:
                verdict = 'suspicious'
                confidence = 50 + (avg_trust - 0.3) * 125  # 50~100%
            else:
                verdict = 'malicious'
                confidence = 90 + (1 - avg_trust / 0.3) * 10  # 90~100% (위험도)
            
            # 5. 결과 반환
            result = {
                'verdict': verdict,
                'confidence': round(confidence, 2),
                'details': {
                    'avg_trust_score': round(avg_trust, 4),
                    'max_trust_score': round(max_trust, 4),
                    'min_trust_score': round(min_trust, 4),
                    'total_reviews': len(reviews),
                    'device': str(self.device),
                    'model': 'KcELECTRA-base-v2022'
                }
            }
            
            logger.info(f"✅ AI 분석 완료: {verdict} (신뢰도 평균: {avg_trust:.4f})")

            return result
            
        except Exception as e:
            logger.error(f"❌ 분석 실패: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def run(self, reviews):
        """
        전체 분석 파이프라인 실행
        
        Args:
            reviews: 원본 리뷰 리스트
        
        Returns:
            분석 결과
        """
        # 1. 모델 로드 (필요시)
        if self.model is None:
            if not self.load_model():
                return {
                    'verdict': 'error',
                    'confidence': 0,
                    'error': '모델 로딩 실패'
                }
        
        # 2. 전처리
        processed_reviews = self.preprocess_reviews(reviews)
        
        if not processed_reviews:
            return {
                'verdict': 'error',
                'confidence': 0,
                'error': '분석할 리뷰가 없습니다'
            }
        
        # 3. 분석
        result = self.analyze_reviews(processed_reviews)
        
        return result


def main():
    """메인 함수 (CLI 실행)"""
    parser = argparse.ArgumentParser(description='리뷰 AI 분석기 (KcELECTRA)')
    parser.add_argument('--input', type=str, help='입력 JSON 파일 경로')
    parser.add_argument('--output', type=str, help='출력 JSON 파일 경로')
    parser.add_argument('--model', type=str, default='ai_models', help='모델 디렉토리')
    
    args = parser.parse_args()
    
    try:
        # 1. 입력 읽기
        if args.input:
            # 파일에서 읽기
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # stdin에서 읽기
            data = json.load(sys.stdin)
        
        reviews = data.get('reviews', [])
        
        if not reviews:
            raise ValueError("리뷰 데이터가 비어있습니다")
        
        # 2. 분석 실행
        analyzer = ReviewAIAnalyzer(model_path=args.model)
        result = analyzer.run(reviews)
        
        # 3. 결과 출력
        output_data = {
            'success': True,
            'result': result
        }
        
        if args.output:
            # 파일에 저장
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            logger.info(f"결과 저장: {args.output}")
        else:
            # stdout에 출력
            print(json.dumps(output_data, ensure_ascii=False))
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"실행 오류: {e}")
        import traceback
        traceback.print_exc()
        
        error_data = {
            'success': False,
            'error': str(e)
        }
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)
        else:
            print(json.dumps(error_data, ensure_ascii=False))
        
        sys.exit(1)


if __name__ == "__main__":
    main()