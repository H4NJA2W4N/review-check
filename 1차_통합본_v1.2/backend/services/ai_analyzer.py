"""
AI 리뷰 분석기 (독립 실행)
입력: JSON (stdin 또는 파일)
출력: JSON (stdout)
"""
import re
import sys
import json
import argparse
from pathlib import Path
import logging
import io

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
    """리뷰 AI 분석기 (KcELECTRA 기반)"""
    
    def __init__(self, model_path="ai_models", retrain_model_path="scripts/ai_models_retrained"):
        # 프로젝트 루트 기준 모델 경로 설정
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent
        self.base_model_path = project_root / model_path
        self.retrain_root = project_root / retrain_model_path
        self.model_path = self.get_latest_model_path() # 최신 모델 쓸 때
        #self.model_path = self.base_model_path # 기존 모델 쓸 때

        self.model = None
        self.tokenizer = None
        self.device = None
        
        logger.info(f"AI 분석기 초기화: {self.model_path}")

    def get_latest_model_path(self):
        """재학습된 모델 중 가장 최신 버전을 자동 선택"""
        try:
            if not self.retrain_root.exists():
                logger.warning("재학습 모델 폴더 없음 → 기본 모델 사용")
                return self.base_model_path

            # 재학습 폴더 안의 model_YYYYMMDD_HHMMSS 같은 폴더 모두 가져오기
            model_dirs = [
                d for d in self.retrain_root.iterdir()
                if d.is_dir() and re.match(r"model_\d{8}_\d{6}", d.name)
            ]

            if not model_dirs:
                logger.warning("재학습 모델 없음 → 기본 모델 사용")
                return self.base_model_path

            # 가장 최근 모델 선택
            latest = max(model_dirs, key=lambda d: d.stat().st_mtime)

            logger.info(f"📌 최신 재학습 모델 선택됨: {latest}")
            return latest

        except Exception as e:
            logger.error(f"❌ 최신 모델 탐색 실패: {e}")
            return self.base_model_path

    def load_model(self):
        """AI 모델 로드"""
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            logger.info("AI 모델 로딩 중...")
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path), local_files_only=True)
            self.model = AutoModelForSequenceClassification.from_pretrained(str(self.model_path), local_files_only=True)
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"✅ AI 모델 로딩 완료 (Device: {self.device})")
            return True
        except Exception as e:
            logger.error(f"❌ 모델 로딩 실패: {e}")
            return False
    
    def preprocess_reviews(self, reviews):
        """전처리: 텍스트가 있는 리뷰만 추출"""
        processed = []
        for review in reviews:
            # text나 content 키가 섞여있을 수 있으므로 둘 다 확인
            text = review.get('text', '') or review.get('content', '')
            if not text: continue
            
            # 원본 데이터 보존하며 text 필드 통일
            item = review.copy()
            item['text'] = text.strip()
            processed.append(item)
            
        return processed
    
    def analyze_reviews(self, reviews):
        """리뷰 분석 수행 및 개별 점수 마킹"""
        try:
            import torch
            import torch.nn.functional as F
            
            logger.info(f"AI 분석 시작: {len(reviews)}개 리뷰")
            
            texts = [r['text'] for r in reviews]
            batch_size = 32
            all_trust_scores = []
            
            # 배치 단위 추론 (속도 최적화)
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                
                inputs = self.tokenizer(
                    batch_texts,
                    return_tensors="pt",
                    truncation=True,
                    max_length=128,
                    padding=True
                ).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    probs = F.softmax(outputs.logits, dim=-1)
                    # 1번 클래스(신뢰/긍정) 확률 추출
                    trust_probs = probs[:, 1].cpu().tolist()
                    all_trust_scores.extend(trust_probs)
            
            # ---------------------------------------------------------
            # [핵심 수정] 개별 리뷰에 점수 및 라벨/색상 부착
            # ---------------------------------------------------------
            enriched_reviews = []
            for i, review in enumerate(reviews):
                score = all_trust_scores[i] * 100  # 0~100점 변환
                
                # 라벨링 및 색상 결정 (요청하신 기준)
                if score >= 76:
                    label = "매우 도움됨"
                    color = "status-green"
                elif score >= 36:
                    label = "부분적으로 도움됨"
                    color = "status-orange"
                else:
                    label = "도움 안됨"
                    color = "status-red"
                
                # 기존 리뷰 데이터에 새 필드 추가
                review['reliability_score'] = round(score, 1)
                review['analysis_label'] = label
                review['color_class'] = color
                
                enriched_reviews.append(review)
            
            # 전체 통계 계산 (평균 신뢰도)
            avg_trust = sum(all_trust_scores) / len(all_trust_scores) if all_trust_scores else 0
            
            # 전체 판정 (Verdict)
            if avg_trust > 0.7:
                verdict = 'safe'
                confidence = avg_trust * 100
            elif avg_trust >= 0.3:
                verdict = 'suspicious'
                confidence = 50 + (avg_trust - 0.3) * 125
            else:
                verdict = 'malicious'
                confidence = 90 + (1 - avg_trust / 0.3) * 10
            
            result = {
                'verdict': verdict,
                'confidence': round(confidence, 2),
                'enriched_reviews': enriched_reviews,  # 점수가 포함된 전체 리스트 반환
                'details': {
                    'avg_trust_score': round(avg_trust, 4),
                    'total_reviews': len(reviews)
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"❌ 분석 실패: {e}")
            raise
    
    def run(self, reviews):
        if self.model is None:
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
    parser.add_argument('--model', type=str, default='ai_models')
    args = parser.parse_args()
    
    try:
        if args.input:
            with open(args.input, 'r', encoding='utf-8') as f: data = json.load(f)
        else:
            data = json.load(sys.stdin)
        
        reviews = data.get('reviews', [])
        
        analyzer = ReviewAIAnalyzer(model_path=args.model)
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