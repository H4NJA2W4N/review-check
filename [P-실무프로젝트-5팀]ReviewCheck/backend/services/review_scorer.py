import torch
import numpy as np
import joblib
import os
import sys
from pathlib import Path
from transformers import AutoTokenizer, AutoModel

class SmartReviewScorer:
    def __init__(self, model_path="final_perfect_scorer.pkl", use_retrained=True):
        # 1. 장치 설정
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[ReviewScorer] Model loading on {self.device}...", file=sys.stderr)

        # 2. KcELECTRA 로드 (기본 모델 고정)
        self.model_name = "beomi/KcELECTRA-base"
        print(f"[ReviewScorer] Loading KcELECTRA: {self.model_name}", file=sys.stderr)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.bert_model = AutoModel.from_pretrained(self.model_name).to(self.device)
            self.bert_model.eval()
        except Exception as e:
            print(f"[Error] KcELECTRA Load Failed: {e}", file=sys.stderr)
            raise

        # 3. Random Forest 모델 경로 결정
        if use_retrained:
            rf_path = self._get_latest_rf_model()
            if rf_path:
                model_path = rf_path
                print(f"[ReviewScorer] Using retrained RF: {model_path}", file=sys.stderr)
            else:
                print(f"[ReviewScorer] No retrained RF found, using base: {model_path}", file=sys.stderr)
        
        # 4. 모델 경로를 절대 경로로 변환
        if not os.path.isabs(model_path):
            # 상대 경로면 절대 경로로 변환
            current_file = Path(__file__).resolve()
            if current_file.parent.name == 'services':
                backend_root = current_file.parent.parent
            else:
                backend_root = current_file.parent
            
            # ai_models/final_perfect_scorer.pkl 형식인 경우
            model_path = str(backend_root / model_path)
        
        # 5. Random Forest 모델 로드
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"[Error] Model file not found: {model_path}")
        
        self.rf_model = joblib.load(model_path)
        print(f"[ReviewScorer] ✅ RF model loaded: {model_path}", file=sys.stderr)

        # 5. 키워드 정의
        self.PRODUCT_KEYWORDS = [
            '두께', '두껍', '얇', '시보리', '지퍼', '마감', '박음질', '실밥','손상',
            '보들', '부드럽', '거칠', '까끌', '탄탄', '짱짱', '퀄리', '재질',
            '소재', '원단', '털', '보풀', '비침', '안감', '주머니', '단추', '버튼',
            '신축성', '스판', '구김', '물빠짐', '세탁', '건조', '냄새', '향', '오염',
            '핏', '기장', '소매', '허리', '어깨', '가슴', '품', '통',
            '오버', '루즈', '슬림', '타이트', '넉넉', '작아', '커요', '길어', '짧아',
            '넓어', '좁아', '딱 맞', '헐렁', '쪼이', '작네', '크네', '길네', '짧네', '맞네',
            '사이즈', '크기', 'cm', 'kg', '키', '몸무게', '평소','크네요','커서','작네요',
            '불편', '편안', '아프', '따뜻', '시원', '여름', '겨울', '가을', '봄', '계절',
            '입어보', '신어보', '써보', '사용해', '착용','따뜻',
            '발볼', '발등', '굽', '무게', '가볍', '무겁', '소음', '소리', '조립', '설치','신발끈',
            '색감', '색상', '실물', '퀄리티','실제'
        ]

        self.DELIVERY_KEYWORDS = [
            "배송", "택배", "기사", "박스", "포장", "주문", "도착", "배송비", "칼배송"
        ]

    def _get_latest_rf_model(self):
        """재학습된 RF 모델 중 가장 최신 버전 찾기"""
        try:
            # 경로 계산
            current_file = Path(__file__).resolve()
            
            # services/review_scorer.py -> backend/ 경로
            if current_file.parent.name == 'services':
                backend_root = current_file.parent.parent  # services -> backend
            else:
                backend_root = current_file.parent  # 직접 backend에 있는 경우
            
            retrain_root = backend_root / "scripts" / "rf_models_retrained"
            
            print(f"[ReviewScorer] Backend root: {backend_root}", file=sys.stderr)
            print(f"[ReviewScorer] Searching for retrained models in: {retrain_root}", file=sys.stderr)
            
            if not retrain_root.exists():
                print(f"[ReviewScorer] Retrain folder not found: {retrain_root}", file=sys.stderr)
                return None
            
            # model_YYYYMMDD_HHMMSS 폴더 찾기
            import re
            model_dirs = [
                d for d in retrain_root.iterdir()
                if d.is_dir() and re.match(r"model_\d{8}_\d{6}", d.name)
            ]
            
            if not model_dirs:
                print(f"[ReviewScorer] No retrained model folders found", file=sys.stderr)
                return None
            
            # 가장 최근 모델 선택
            latest = max(model_dirs, key=lambda d: d.stat().st_mtime)
            model_file = latest / "random_forest_model.pkl"
            
            if model_file.exists():
                print(f"[ReviewScorer] ✅ Found latest retrained RF: {latest.name}", file=sys.stderr)
                print(f"[ReviewScorer] Model path: {model_file}", file=sys.stderr)
                return str(model_file)
            else:
                print(f"[ReviewScorer] Model file not found in {latest.name}", file=sys.stderr)
            
            return None
            
        except Exception as e:
            print(f"[Warning] Failed to find retrained RF: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return None
    
    def _resolve_model_path(self, model_path):
        """상대 경로를 절대 경로로 변환"""
        path = Path(model_path)
        
        # 이미 절대 경로면 그대로 반환
        if path.is_absolute():
            return str(path)
        
        # 상대 경로면 backend 기준으로 변환
        current_file = Path(__file__).resolve()
        if current_file.parent.name == 'services':
            backend_root = current_file.parent.parent
        else:
            backend_root = current_file.parent
        
        absolute_path = backend_root / path
        return str(absolute_path)

    def _extract_features(self, text):
        """771차원 특징 추출 (768 + 3)"""
        text = str(text)
        
        # KcELECTRA 임베딩
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=128).to(self.device)
        with torch.no_grad():
            emb = self.bert_model(**inputs).last_hidden_state[:, 0, :].cpu().numpy()[0]
        
        # 추가 피처
        length_val = min(len(text), 100) / 100.0
        has_product = 1 if any(k in text for k in self.PRODUCT_KEYWORDS) else 0
        has_delivery = 1 if any(k in text for k in self.DELIVERY_KEYWORDS) else 0
        
        # 결합 (768 + 3 = 771)
        return np.hstack([emb.reshape(1, -1), np.array([[length_val, has_product, has_delivery]])]), length_val, has_product, has_delivery

    def predict(self, text):
        if not text: return 0.0
        features, length_val, has_product, has_delivery = self._extract_features(text)
        
        # AI 예측
        probs = self.rf_model.predict_proba(features)[0]
        raw_score = probs[1] * 100
        
        # 키워드 기반 점수 조정
        final_score = raw_score
        
        # (Rule 1) 상품 키워드 없음 -> 25% 수준으로 폭락
        if has_product == 0:
            final_score = raw_score * 0.25
        
        # (Rule 2) 배송무새 -> 10% 수준으로 폭락
        elif has_delivery == 1 and length_val < 0.2:
            final_score = final_score * 0.1
            
        else:
            # 정상 케이스 -> 길이 가산점
            length_bonus = min(len(text), 50) / 50.0
            final_score = (final_score * 0.85) + (final_score * 0.15 * length_bonus)
            
        return round(final_score, 1)

if __name__ == "__main__":
    scorer = SmartReviewScorer()
    print(f"Test Score: {scorer.predict('사이즈가 딱 맞아요')}", file=sys.stderr)