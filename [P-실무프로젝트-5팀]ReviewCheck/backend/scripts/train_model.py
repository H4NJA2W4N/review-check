"""
Random Forest 모델 재학습 스크립트
원본 학습 데이터 + 피드백 데이터를 병합하여 전체 재학습
"""
import os
import sys
import time
import logging
import torch
import joblib
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from transformers import AutoTokenizer, AutoModel
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd

# backend 경로 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from models.database import SessionLocal
from models.ai_job import AIJob
from models.ai_model import AIModel
from models.feedback import Feedback

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('train_model.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ⭐ 원본 학습 데이터 경로 설정
# AI 팀원에게 받은 CSV 파일 경로
ORIGINAL_DATA_PATH = "ai_models/original_training_data.csv"


class FeatureExtractor:
    """KcELECTRA를 사용한 특징 추출기"""
    
    def __init__(self, model_name="beomi/KcELECTRA-base"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"디바이스: {self.device}")
        
        logger.info(f"KcELECTRA 로딩: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.bert_model = AutoModel.from_pretrained(model_name).to(self.device)
        self.bert_model.eval()
        
        # 키워드 정의 (review_scorer.py와 동일)
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
    
    def extract_features(self, text):
        """텍스트에서 771차원 특징 추출"""
        text = str(text)
        
        # 1. KcELECTRA 임베딩 (768차원)
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            padding="max_length", 
            max_length=128
        ).to(self.device)
        
        with torch.no_grad():
            emb = self.bert_model(**inputs).last_hidden_state[:, 0, :].cpu().numpy()[0]
        
        # 2. 추가 피처 (3차원)
        length_val = min(len(text), 100) / 100.0
        has_product = 1 if any(k in text for k in self.PRODUCT_KEYWORDS) else 0
        has_delivery = 1 if any(k in text for k in self.DELIVERY_KEYWORDS) else 0
        
        # 3. 결합 (768 + 3 = 771)
        features = np.hstack([emb, np.array([length_val, has_product, has_delivery])])
        
        return features


def load_original_data():
    """
    AI 팀원이 제공한 원본 학습 데이터 로드
    
    Returns:
        DataFrame with columns: text, label
    """
    backend_root = Path(__file__).parent.parent
    original_path = backend_root / ORIGINAL_DATA_PATH
    
    if not original_path.exists():
        logger.warning(f"원본 학습 데이터 없음: {original_path}")
        logger.warning("   AI 팀원에게 original_training_data.csv 파일을 요청하세요.")
        logger.warning("   파일 위치: backend/ai_models/original_training_data.csv")
        logger.warning("   파일 형식: text,label 컬럼")
        return None
    
    logger.info(f"원본 학습 데이터 로딩: {original_path}")
    
    try:
        df = pd.read_csv(original_path)
        
        # 컬럼 검증
        if 'text' not in df.columns or 'label' not in df.columns:
            logger.error("CSV 파일에 'text', 'label' 컬럼이 필요합니다!")
            return None
        
        logger.info(f"원본 데이터 로딩 완료: {len(df)}개")
        logger.info(f"   - 라벨 1: {(df['label'] == 1).sum()}개")
        logger.info(f"   - 라벨 0: {(df['label'] == 0).sum()}개")
        
        return df
        
    except Exception as e:
        logger.error(f"원본 데이터 로딩 실패: {e}")
        return None


def load_feedback_data(db: Session):
    """
    DB에서 피드백 데이터 로드
    
    Returns:
        DataFrame with columns: text, label
    """
    logger.info("피드백 데이터 로딩 중...")
    
    feedbacks = db.query(Feedback).all()
    
    if not feedbacks:
        logger.warning("피드백 데이터가 없습니다.")
        return None
    
    data = {
        'text': [f.review_text for f in feedbacks],
        'label': [f.tags for f in feedbacks]
    }
    
    df = pd.DataFrame(data)
    logger.info(f"피드백 데이터 로딩 완료: {len(df)}개")
    logger.info(f"   - 라벨 1 (도움됨): {(df['label'] == 1).sum()}개")
    logger.info(f"   - 라벨 0 (부족함): {(df['label'] == 0).sum()}개")
    
    return df


def combine_data(original_df, feedback_df):
    """
    원본 데이터와 피드백 데이터 병합
    
    Returns:
        DataFrame with columns: text, label, source
    """
    logger.info("\n" + "="*60)
    logger.info("데이터 병합")
    logger.info("="*60)
    
    datasets = []
    
    if original_df is not None and len(original_df) > 0:
        original_df = original_df.copy()
        original_df['source'] = 'original'
        datasets.append(original_df)
        logger.info(f"원본 데이터: {len(original_df)}개")
    
    if feedback_df is not None and len(feedback_df) > 0:
        feedback_df = feedback_df.copy()
        feedback_df['source'] = 'feedback'
        datasets.append(feedback_df)
        logger.info(f"피드백 데이터: {len(feedback_df)}개")
    
    if not datasets:
        raise ValueError("병합할 데이터가 없습니다!")
    
    # 병합
    combined_df = pd.concat(datasets, ignore_index=True)
    
    logger.info(f"\n병합 완료: 총 {len(combined_df)}개")
    logger.info(f"   - 원본: {len(combined_df[combined_df['source'] == 'original'])}개")
    logger.info(f"   - 피드백: {len(combined_df[combined_df['source'] == 'feedback'])}개")
    logger.info(f"   - 라벨 1: {(combined_df['label'] == 1).sum()}개")
    logger.info(f"   - 라벨 0: {(combined_df['label'] == 0).sum()}개")
    logger.info("="*60 + "\n")
    
    return combined_df


def train_random_forest(job_id: int, output_dir: str):
    """
    Random Forest 모델 재학습 (원본 + 피드백 데이터)
    
    Args:
        job_id: 작업 ID
        output_dir: 새 모델 저장 경로
    """
    db = SessionLocal()
    
    try:
        # 1. 작업 상태 업데이트
        job = db.query(AIJob).filter(AIJob.job_id == job_id).first()
        job.status = 'running'
        job.started_at = datetime.now(timezone.utc)
        job.logs = f"{job.logs}\n[{datetime.now()}] Random Forest 재학습 시작..."
        db.commit()
        
        logger.info(f"재학습 시작: job_id={job_id}")
        
        # 2. 데이터 로드 및 병합
        original_df = load_original_data()
        feedback_df = load_feedback_data(db)
        
        combined_df = combine_data(original_df, feedback_df)
        
        # ⭐ 최소 데이터 체크 (원본 포함하므로 완화됨)
        if len(combined_df) < 100:
            error_msg = f"전체 데이터 부족: {len(combined_df)}개 (최소 100개 필요)"
            logger.error(error_msg)
            
            job.status = 'failed'
            job.finished_at = datetime.utcnow()
            job.error_message = error_msg
            job.logs = f"{job.logs}\n[{datetime.now()}] {error_msg}"
            db.commit()
            
            return {'success': False, 'error': error_msg}
        
        # 데이터 품질 체크
        label_1_count = (combined_df['label'] == 1).sum()
        label_0_count = (combined_df['label'] == 0).sum()
        label_1_ratio = label_1_count / len(combined_df)
        
        logger.info(f"라벨 분포: 1={label_1_count}개 ({label_1_ratio*100:.1f}%), 0={label_0_count}개")
        
        if label_1_count < 5 or label_0_count < 5:
            error_msg = f"한쪽 라벨이 너무 적음: label=1 {label_1_count}개, label=0 {label_0_count}개"
            logger.error(error_msg)
            
            job.status = 'failed'
            job.finished_at = datetime.utcnow()
            job.error_message = error_msg
            job.logs = f"{job.logs}\n[{datetime.now()}] {error_msg}"
            db.commit()
            
            return {'success': False, 'error': error_msg}
        
        # 데이터 샘플 표시 (피드백 데이터 위주로)
        logger.info("\n" + "="*60)
        logger.info("피드백 데이터 샘플 (최근 5개)")
        logger.info("="*60)
        feedback_samples = combined_df[combined_df['source'] == 'feedback'].tail(5)
        for idx, row in feedback_samples.iterrows():
            text_preview = row['text'][:50] + "..." if len(row['text']) > 50 else row['text']
            logger.info(f"[{idx+1}] Label={row['label']}: {text_preview}")
        logger.info("="*60 + "\n")
        
        # 3. 특징 추출
        logger.info("KcELECTRA로 특징 추출 중...")
        extractor = FeatureExtractor()
        
        features_list = []
        labels_list = []
        
        for idx, row in combined_df.iterrows():
            features = extractor.extract_features(row['text'])
            features_list.append(features)
            labels_list.append(row['label'])
            
            # 진행률 표시
            if (idx + 1) % 500 == 0:
                logger.info(f"   진행: {idx + 1}/{len(combined_df)}")
        
        X = np.array(features_list)
        y = np.array(labels_list)
        
        logger.info(f"특징 추출 완료: X shape={X.shape}, y shape={y.shape}")
        
        # 4. 학습/검증 데이터 분할
        X_train, X_val, y_train, y_val = train_test_split(
            X, y,
            test_size=0.2,
            random_state=42,
            stratify=y
        )
        logger.info(f"데이터 분할: 학습={len(X_train)}, 검증={len(X_val)}")
        
        # 5. Random Forest 학습
        logger.info("\n" + "="*60)
        logger.info("Random Forest 학습 중...")
        logger.info("="*60)
        
        rf_model = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=10,
            min_samples_leaf=5,
            max_features='sqrt',
            bootstrap=True,
            random_state=42,
            n_jobs=-1
        )
        
        rf_model.fit(X_train, y_train)
        
        # 6. 평가
        logger.info("\n" + "="*60)
        logger.info("모델 평가")
        logger.info("="*60)
        
        train_acc = accuracy_score(y_train, rf_model.predict(X_train))
        val_acc = accuracy_score(y_val, rf_model.predict(X_val))
        
        cv_scores = cross_val_score(rf_model, X, y, cv=min(5, len(X)//4))
        cv_mean = cv_scores.mean()
        cv_std = cv_scores.std()
        
        logger.info(f"학습 정확도: {train_acc:.4f}")
        logger.info(f"검증 정확도: {val_acc:.4f}")
        logger.info(f"교차 검증: {cv_mean:.4f} (±{cv_std:.4f})")
        
        # 성능 경고
        if val_acc < 0.7:
            logger.warning("검증 정확도가 기대보다 낮습니다 (70% 미만)")
        
        if train_acc - val_acc > 0.15:
            logger.warning("오버피팅 감지 (학습-검증 정확도 차이 > 15%)")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"학습 완료 요약")
        logger.info(f"   - 전체 데이터: {len(X)}개")
        logger.info(f"   - 학습 샘플: {len(X_train)}개")
        logger.info(f"   - 검증 샘플: {len(X_val)}개")
        logger.info(f"   - 검증 정확도: {val_acc:.4f}")
        logger.info(f"   - 교차 검증: {cv_mean:.4f}")
        logger.info(f"{'='*60}\n")
        
        # 7. 모델 저장
        os.makedirs(output_dir, exist_ok=True)
        model_path = os.path.join(output_dir, "random_forest_model.pkl")
        
        logger.info(f"모델 저장: {model_path}")
        joblib.dump(rf_model, model_path)
        
        # 8. 메타데이터 저장
        metadata = {
            'total_samples': len(X),
            'original_samples': len(original_df) if original_df is not None else 0,
            'feedback_samples': len(feedback_df) if feedback_df is not None else 0,
            'train_samples': len(X_train),
            'val_samples': len(X_val),
            'train_accuracy': float(train_acc),
            'val_accuracy': float(val_acc),
            'cv_accuracy': float(cv_mean),
            'cv_std': float(cv_std),
            'n_features': X.shape[1],
            'n_estimators': rf_model.n_estimators,
            'max_depth': rf_model.max_depth,
            'label_distribution': {
                'positive': int(label_1_count),
                'negative': int(label_0_count)
            },
            'created_at': datetime.now().isoformat(),
            'kcelectra_model': 'beomi/KcELECTRA-base',
            'training_mode': 'original_plus_feedback'
        }
        
        import json
        metadata_path = os.path.join(output_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 9. 작업 완료 처리
        job.status = 'completed'
        job.finished_at = datetime.utcnow()
        job.logs = f"{job.logs}\n[{datetime.now()}] 학습 완료!\n전체 데이터: {len(X)}개\n검증 정확도: {val_acc:.4f}\n교차 검증: {cv_mean:.4f}"
        db.commit()
        
        logger.info(f"재학습 완료: job_id={job_id}")
        
        return {
            'success': True,
            'accuracy': float(val_acc),
            'cv_accuracy': float(cv_mean),
            'metadata': metadata
        }
        
    except Exception as e:
        logger.error(f"재학습 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        job = db.query(AIJob).filter(AIJob.job_id == job_id).first()
        if job:
            job.status = 'failed'
            job.finished_at = datetime.utcnow()
            job.error_message = str(e)
            job.logs = f"{job.logs}\n[{datetime.now()}] 학습 실패: {str(e)}"
            db.commit()
        
        return {'success': False, 'error': str(e)}
        
    finally:
        db.close()


def create_new_model_version(db: Session, old_model: AIModel, accuracy: float, output_dir: str):
    """새 모델 버전 생성"""
    try:
        old_version = old_model.version
        major, minor = old_version.replace('v', '').split('.')
        new_version = f"v{major}.{int(minor) + 1}"
        
        logger.info(f"새 모델 버전 생성: {old_version} → {new_version}")
        
        # 절대 경로 → 상대 경로 변환
        output_path = Path(output_dir)
        backend_root = Path(__file__).parent.parent
        
        try:
            relative_path = output_path.relative_to(backend_root)
            artifact_url = str(relative_path).replace('\\', '/')
        except ValueError:
            artifact_url = output_dir
        
        logger.info(f"DB 저장 경로: {artifact_url}")
        
        new_model = AIModel(
            model_name="RandomForest-review-scorer",
            version=new_version,
            artifact_url=artifact_url,
            description=f"재학습 모델 - 원본+피드백 ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
            accuracy=accuracy,
            active=True
        )
        db.add(new_model)
        
        old_model.active = False
        
        db.commit()
        db.refresh(new_model)
        
        logger.info(f"새 모델 등록 완료: model_id={new_model.model_id}")
        
        return new_model
        
    except Exception as e:
        logger.error(f"모델 버전 생성 실패: {e}")
        db.rollback()
        raise


def check_and_process_jobs():
    """pending 상태의 재학습 작업 확인 및 처리"""
    db = SessionLocal()
    
    try:
        pending_jobs = db.query(AIJob).filter(
            AIJob.type == 'training',
            AIJob.status == 'pending'
        ).order_by(AIJob.submitted_at).all()
        
        if not pending_jobs:
            logger.debug("대기 중인 작업 없음")
            return
        
        logger.info(f"대기 중인 재학습 작업: {len(pending_jobs)}개")
        
        for job in pending_jobs:
            logger.info(f"\n{'='*60}")
            logger.info(f"작업 처리: job_id={job.job_id}")
            logger.info(f"{'='*60}")
            
            current_model = db.query(AIModel).filter(AIModel.active == True).first()
            
            if not current_model:
                logger.error("활성 모델이 없습니다!")
                job.status = 'failed'
                job.error_message = "활성 모델 없음"
                db.commit()
                continue
            
            # 새 모델 저장 경로
            backend_root = Path(__file__).parent.parent
            output_dir = backend_root / "scripts" / "rf_models_retrained" / f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            output_dir = str(output_dir)
            
            logger.info(f"모델 저장 경로: {output_dir}")
            
            # 재학습 수행
            result = train_random_forest(
                job_id=job.job_id,
                output_dir=output_dir
            )
            
            if result['success']:
                new_model = create_new_model_version(
                    db,
                    current_model,
                    result.get('accuracy', 0),
                    output_dir
                )
                
                logger.info(f"재학습 완료: {current_model.version} → {new_model.version}")
            else:
                logger.error(f"재학습 실패: {result.get('error', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"작업 처리 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()


def main():
    logger.info("="*60)
    logger.info("Random Forest 재학습 스크립트 시작")
    logger.info("학습 방식: 원본 학습 데이터 + 피드백 데이터 병합")
    logger.info("="*60)
    
    if torch.cuda.is_available():
        logger.info(f"GPU 감지됨: {torch.cuda.get_device_name(0)}")
        # ✅ 시작 시 GPU 메모리 초기화
        torch.cuda.empty_cache()
        logger.info("초기 GPU 메모리 정리 완료")
    else:
        logger.warning("GPU를 찾을 수 없습니다. CPU로 동작합니다.")

    logger.info("==========================================")

    try:
        check_and_process_jobs()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("최종 GPU 메모리 정리")
        
        logger.info("작업 완료 - 프로그램 종료")

    except Exception as e:
        logger.error(f"메인 루프 치명적 오류: {e}")
        # ✅ 에러 발생 시에도 GPU 메모리 해제
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("에러 후 GPU 메모리 정리")
        logger.error("작업 실패 - 프로그램 종료")
        sys.exit(1)  # 에러 코드로 종료
        
    


if __name__ == "__main__":
    main()