"""Create audit_log table for security audit logging."""
import sys

sys.path.insert(0, 'src')

import pymysql

from config.settings import Config

conn = pymysql.connect(
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    database=Config.DB_NAME,
    charset=Config.DB_CHARSET
)

cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    username VARCHAR(50),
    action VARCHAR(50) NOT NULL,
    detail VARCHAR(500),
    ip VARCHAR(45),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
)
''')
conn.commit()
print("OK: audit_log table created")

cur.close()
conn.close()
print("Migration complete!")
