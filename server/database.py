import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

config = {
    'host': os.getenv('TIDB_HOST', '127.0.0.1'),
    'port': int(os.getenv('TIDB_PORT', '4000')),
    'user': os.getenv('TIDB_USER', 'root'),
    'password': os.getenv('TIDB_PASSWORD', ''),
    'database': os.getenv('TIDB_DATABASE', 'quoter'),
    'ssl_mode': os.getenv('TIDB_SSL_MODE', 'VERIFY_IDENTITY'),
    'pool_name': 'tidb_pool',
    'pool_size': 5,
}

pool = None

def get_pool():
    global pool
    if pool is None:
        pool = pooling.MySQLConnectionPool(**config)
    return pool

def get_connection():
    return get_pool().get_connection()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    with open(os.path.join(os.path.dirname(__file__), 'schema.sql')) as f:
        for statement in f.read().split(';'):
            s = statement.strip()
            if s:
                cursor.execute(s + ';')
    conn.commit()
    cursor.close()
    conn.close()
