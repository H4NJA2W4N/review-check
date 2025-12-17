#
# JWT 토큰 및 비밀번호 처리를 위한 인증 서비스
#

import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS, SERVER_BOOT_TIME

def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"❌ 비밀번호 검증 오류: {e}")
        return False

def create_access_token(username: str) -> tuple[str, datetime]:
    """
    JWT 액세스 토큰 생성
    Returns: (token, expires_at)
    """
    expires_at = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode = {
        "sub": username,  # subject: 관리자 username
        "exp": expires_at,  # expiration: 만료 시간
        "iat": datetime.utcnow()  # issued at: 발급 시간
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expires_at

def verify_token(token: str) -> str | None:
    """
    JWT 토큰 검증
    Returns: username or None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_iat = payload.get("iat")
        
        if username is None or token_iat is None:
            return None
        token_iat_dt = datetime.utcfromtimestamp(token_iat)
        
        # 🔥 서버 부팅 이후 발급된 토큰만 유효
        if token_iat_dt < SERVER_BOOT_TIME:
            print("❌ 서버 재시작 이후 이전 토큰 사용 → 무효 처리됨")
            return None
        
        return username
    except JWTError as e:
        print(f"❌ 토큰 검증 실패: {e}")
        return None

def extract_token_from_header(authorization: str) -> str | None:
    """
    Authorization 헤더에서 토큰 추출
    Format: "Bearer {token}"
    """
    try:
        if not authorization or not authorization.startswith("Bearer "):
            return None
        return authorization.split(" ")[1]
    except Exception:
        return None