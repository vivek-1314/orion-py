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
        print("✅  DB pool initialized")
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

def fetch_identity_memory(user_id , what_exact_memory: str):
    """
    Fetch only the `what_exact_memory` field from identity table for a given user.
    Fallback: If column doesn't exist, fetch from JSONB array `identity_facts`.
    """
    print("Fetching identity memory for user:", user_id, "key:", what_exact_memory)
    conn = None
    try:
        conn = get_conn()  # get connection from pool
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # First, try to fetch the direct column
        try : 
            query = sql.SQL("SELECT {field} FROM identity WHERE user_id = %s").format(
            field=sql.Identifier(what_exact_memory)
            )
            cur.execute(query, (user_id,))
            result = cur.fetchone()
            return result
        except Exception as e:  
            print("Error fetching identity memory:", e)
            conn.rollback() 

        # Fallback: fetch identity_facts JSONB array and search for key
        print("Falling back to identity_facts JSONB array")
        cur.execute("SELECT identity_facts FROM identity WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        if result and result.get("identity_facts"):
            facts = result["identity_facts"]
            # If JSON stored as string, parse it
            if isinstance(facts, str):
                facts = json.loads(facts)
            # Search for key
            if isinstance(facts, dict):
                if what_exact_memory in facts:
                    cur.close()
                    return facts[what_exact_memory]

        cur.close()
        return None

    except Exception as e:
        print("IDENTITY FETCH ERROR:", e)
        return None
    finally:
        if conn:
            release_conn(conn)  # return connection to pool