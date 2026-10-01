
import os
import sys

import pymysql
from dotenv import load_dotenv

load_dotenv()

# 默认值与 config.settings 对齐（#28）：此前 DB_PASSWORD 默认空串、
# DB_NAME 默认 'wb'，与真实配置三处不一致，连接失败时误导排障
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

try:
    from config.settings import Config

    conn = pymysql.connect(
        host=Config.DB_HOST,
        port=int(Config.DB_PORT),
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset=Config.DB_CHARSET
    )
    print('Database connected OK!')
    with conn.cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM user')
        count = cursor.fetchone()[0]
        print(f'User table has {count} records')
    conn.close()
except Exception as e:
    print(f'Database error: {e}')
