"""
AI 모델 재학습 스크립트
주기적으로 DB를 체크하여 pending 상태의 재학습 작업을 처리
"""
import os
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

import sys
import time
import logging
import torch
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    AutoConfig
)
from torch.utils.data import Dataset
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

# 환경 변수
os.environ["WANDB_DISABLED"] = "true"


class ReviewDataset(Dataset):
    """리뷰 데이터셋"""
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = int(self.labels[idx])
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }


def load_feedback_data(db: Session):
    """
    DB에서 피드백 데이터 로드
    
    Returns:
        DataFrame with columns: text, label
    """
    logger.info("피드백 데이터 로딩 중...")
    
    feedbacks = db.query(Feedback).all()
    
    if not feedbacks:
        raise ValueError("피드백 데이터가 없습니다.")
    
    data = {
        'text': [f.review_text for f in feedbacks],
        'label': [f.tags for f in feedbacks]
    }
    
    df = pd.DataFrame(data)
    logger.info(f"데이터 로딩 완료: {len(df)}개")
    logger.info(f"  - 라벨 1 (도움됨): {(df['label'] == 1).sum()}개")
    logger.info(f"  - 라벨 0 (부족함): {(df['label'] == 0).sum()}개")
    
    return df


def train_model(job_id: int, current_model_path: str, output_dir: str):
    """
    모델 재학습 수행
    
    Args:
        job_id: 작업 ID
        current_model_path: 현재 활성 모델 경로
        output_dir: 새 모델 저장 경로
    """
    db = SessionLocal()
    
    try:
        # 1. 작업 상태 업데이트
        job = db.query(AIJob).filter(AIJob.job_id == job_id).first()
        job.status = 'running'
        job.started_at = datetime.now(timezone.utc)
        job.logs = f"{job.logs}\n[{datetime.now()}] 학습 시작..."
        db.commit()
        
        logger.info(f"재학습 시작: job_id={job_id}")
        
        # 2. 피드백 데이터 로드
        df = load_feedback_data(db)
        
        # 3. 학습/검증 데이터 분할 (8:2)
        from sklearn.model_selection import train_test_split
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            df['text'].values,
            df['label'].values,
            test_size=0.2,
            random_state=42,
            stratify=df['label'].values
        )
        
        logger.info(f"데이터 분할: 학습={len(train_texts)}, 검증={len(val_texts)}")
        
        # 4. 토크나이저 및 모델 로드
        backend_dir = Path(__file__).parent.parent  # scripts/ -> backend/
        project_root = backend_dir.parent  # backend/ -> 프로젝트 루트/
        model_path = Path(current_model_path)
        
        # 상대 경로이면 backend 기준 절대경로로 변환
        if not model_path.is_absolute():
            model_path = project_root / model_path

        # 파일 확인
        if not model_path.exists():
            raise FileNotFoundError(f"모델 경로 없음: {model_path}")
        
        config_file = model_path / "config.json"
        if not config_file.exists():
            raise FileNotFoundError(f"config.json 없음: {config_file}")
        
        logger.info("모델 파일 확인 완료")

        logger.info("Config 로딩 중...")
        # Step 1: Config 먼저 로드
        config = AutoConfig.from_pretrained(
            str(model_path),
            local_files_only=True
        )
        logger.info("Config 로딩 완료")

        logger.info("Tokenizer 로딩 중...")
        tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)

        logger.info("Model 로딩 중...")
        model = AutoModelForSequenceClassification.from_pretrained(
            str(model_path),
            config=config,
            local_files_only=True
        )
        
        logger.info(f"모델 로딩 완료")

        # 5. 데이터셋 생성
        train_dataset = ReviewDataset(train_texts, train_labels, tokenizer)
        val_dataset = ReviewDataset(val_texts, val_labels, tokenizer)
        
        # 6. 학습 설정
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=3,  # 재학습이므로 3 epoch 정도면 충분
            per_device_train_batch_size=16,
            per_device_eval_batch_size=16,
            warmup_steps=100,
            weight_decay=0.01,
            logging_dir=f'{output_dir}/logs',
            logging_steps=10,
            eval_strategy='epoch',
            save_strategy='epoch',
            load_best_model_at_end=True,
            metric_for_best_model='eval_loss',
            save_total_limit=2
        )
        
        # 7. Trainer 생성 및 학습
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset
        )
        
        logger.info("학습 시작...")
        train_result = trainer.train()
        
        # 8. 모델 저장
        logger.info(f"모델 저장: {output_dir}")
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)
        
        # 9. 평가
        eval_result = trainer.evaluate()
        logger.info(f"평가 결과: {eval_result}")
        
        accuracy = 1 - eval_result.get('eval_loss', 0)  # 간단한 추정
        
        # 10. 작업 완료 처리
        job.status = 'completed'
        job.finished_at = datetime.utcnow()
        job.logs = f"{job.logs}\n[{datetime.now()}] 학습 완료!\n평가 결과: {eval_result}"
        db.commit()
        
        logger.info(f"재학습 완료: job_id={job_id}")
        
        return {
            'success': True,
            'accuracy': accuracy,
            'eval_result': eval_result
        }
        
    except Exception as e:
        logger.error(f"재학습 실패: {e}")
        
        # 실패 처리
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
    """
    새 모델 버전 생성
    
    Args:
        db: 데이터베이스 세션
        old_model: 이전 모델
        accuracy: 새 모델 정확도
        output_dir: 새 모델 경로
    """
    try:
        # 버전 증가 (v1.0 -> v1.1, v1.1 -> v1.2, ...)
        old_version = old_model.version  # 예: "v1.0"
        major, minor = old_version.replace('v', '').split('.')
        new_version = f"v{major}.{int(minor) + 1}"
        
        logger.info(f"새 모델 버전 생성: {old_version} → {new_version}")
        
        # 새 모델 레코드 생성
        new_model = AIModel(
            model_name=old_model.model_name,
            version=new_version,
            artifact_url=output_dir,
            description=f"재학습 모델 ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
            accuracy=accuracy,
            active=True  # 새 모델 활성화
        )
        db.add(new_model)
        
        # 이전 모델 비활성화
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
        # pending 상태의 training 작업 조회
        pending_jobs = db.query(AIJob).filter(
            AIJob.type == 'training',
            AIJob.status == 'pending'
        ).order_by(AIJob.submitted_at).all()
        
        if not pending_jobs:
            logger.debug("대기 중인 작업 없음")
            return
        
        logger.info(f"대기 중인 재학습 작업: {len(pending_jobs)}개")
        
        # 각 작업 처리
        for job in pending_jobs:
            logger.info(f"\n{'='*60}")
            logger.info(f"작업 처리: job_id={job.job_id}")
            logger.info(f"{'='*60}")
            
            # 현재 활성 모델 조회
            current_model = db.query(AIModel).filter(AIModel.active == True).first()
            
            if not current_model:
                logger.error("활성 모델이 없습니다!")
                job.status = 'failed'
                job.error_message = "활성 모델 없음"
                db.commit()
                continue
            
            # 새 모델 저장 경로
            output_dir = f"ai_models_retrained/model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(output_dir, exist_ok=True)
            
            # 재학습 수행
            result = train_model(
                job_id=job.job_id,
                current_model_path=current_model.artifact_url,
                output_dir=output_dir
            )
            
            if result['success']:
                # 새 모델 버전 생성
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
    """메인 루프: 주기적으로 재학습 작업 체크"""
    logger.info("="*60)
    logger.info("AI 재학습 스크립트 시작")
    logger.info("="*60)
    
    # 체크 주기 (초): 기본 60초 = 1분
    CHECK_INTERVAL = int(os.getenv('TRAIN_CHECK_INTERVAL', '60'))
    
    logger.info(f"체크 주기: {CHECK_INTERVAL}초")
    
    while True:
        try:
            check_and_process_jobs()
        except Exception as e:
            logger.error(f"메인 루프 오류: {e}")
        
        logger.debug(f"{CHECK_INTERVAL}초 대기 중...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()