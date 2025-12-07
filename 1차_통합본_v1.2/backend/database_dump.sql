-- SQLite 구문 제거
-- PRAGMA foreign_keys=OFF; 삭제
-- BEGIN TRANSACTION; 삭제
-- COMMIT; 삭제

-- 테이블 생성 구문 수정 예시
CREATE TABLE IF NOT EXISTS admin (
    admin_id INTEGER PRIMARY KEY AUTO_INCREMENT,  -- AUTOINCREMENT → AUTO_INCREMENT
    username VARCHAR(50) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- DATETIME → TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notice (
    notice_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    INDEX idx_created_at (created_at)  -- 인덱스 추가
);

CREATE TABLE IF NOT EXISTS inquiry (
    inquiry_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(100) NOT NULL,
    inquiry_type VARCHAR(50),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);

CREATE TABLE IF NOT EXISTS inquiry_reply (
    reply_id INTEGER PRIMARY KEY AUTO_INCREMENT,
    inquiry_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (inquiry_id) REFERENCES inquiry(inquiry_id) ON DELETE CASCADE
);

-- INSERT 구문은 그대로 사용 가능
INSERT INTO admin (admin_id, username, hashed_password, created_at) 
VALUES (1, 'admin', '$2b$12$...', '2024-12-01 10:00:00');