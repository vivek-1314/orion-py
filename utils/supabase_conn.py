import psycopg2
from psycopg2 import pool
import os
from urllib.parse import urlparse
from psycopg2.extras import RealDictCursor 
import json
from psycopg2 import sql

DATABASE_URL = os.environ.get("SUPABASE_URL")  # e.g. your Supabase URL

db_pool = None  # will hold the connection pool

def init_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL,
            sslmode="require"
        )
        print("✅ supabase_DB pool initialized")
    return db_pool

def get_conn():
    global db_pool
    if db_pool is None:
        raise Exception("DB pool not initialized")
    return db_pool.getconn()

def release_conn(conn):
    global db_pool
    if db_pool:
        db_pool.putconn(conn)

def close_pool():
    global db_pool
    if db_pool:
        db_pool.closeall()
        db_pool = None
        print("DB pool closed")