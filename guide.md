1. 기존 모델 파일은 project/ai_models/ 경로에, 최신 학습된 모델은project/backend/scripts/ai_models_retrained/model_.../ 경로에 넣는다.

2. 실행 방법

   프론트엔드

   - project/ 경로에서 필요한 모듈 설치
     - npm install
     - npm install lucide-react

   - project/ 경로에서 실행
     - npm run dev

   백엔드

   - project/backend/ 경로에서 필요한 패키지 설치
     - pip install -r requirements.txt

   - project/backend/ 경로에서 FastAPI 서버 시작
     - uvicorn main:app --reload --port 8000

   재학습 스크립트

   - project/backend/scripts 경로에서 백그라운드로 실행
     
- start "" python train_model.py
     
- 이는 일정 주기마다 재학습 요청이 들어왔는지 데이터베이스를 체크한다.
   
- 재학습 요청이 들어오면 그동안 쌓인 피드백 데이터를 이용하여 KcElectra 모델을 fine-tuning함.
   
- 재학습이 끝나면, DB의 ai_models 테이블에 모델 정보를 추가
   
  
   
   즉, 프론트엔드/백엔드/재학습 스크립트 총 3개의 터미널이 필요함





3. 유의사항
   - 해당 실행 방법은 로컬 환경 기준으로, 학과 서버로 이전시 포트 및 데이터베이스 변경 등에 따라 실행 방법이 바뀔 수 있음
   - 모델을 재학습 하는 행위가 자주 일어나는 것이 아니기 때문에 장점이 있는지는 모르겠음 그냥 재학습이 필요할 때마다 관리자가 수동으로 스크립트 파일을 실행하는 것이 가장 좋을 거 같다.

