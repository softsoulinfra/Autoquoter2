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
    'ssl_disabled': False,
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
    # Use a direct connection (no pool) to create the database
    conn = mysql.connector.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        ssl_disabled=False,
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS quoter CHARACTER SET utf8mb4")
    cursor.execute("USE quoter")
    with open(os.path.join(os.path.dirname(__file__), 'schema.sql')) as f:
        for statement in f.read().split(';'):
            s = statement.strip()
            if s:
                cursor.execute(s + ';')
    conn.commit()
    cursor.close()
    conn.close()
