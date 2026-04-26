
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

try:
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'wb'),
        charset='utf8mb4'
    )
    print('Database connected OK!')
    with conn.cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM user')
        count = cursor.fetchone()[0]
        print(f'User table has {count} records')
    conn.close()
except Exception as e:
    print(f'Database error: {e}')
