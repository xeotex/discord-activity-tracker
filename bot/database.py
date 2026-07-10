import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voice_sessions (
            id SERIAL PRIMARY KEY,
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            join_at BIGINT NOT NULL,
            leave_at BIGINT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS archived_totals (
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            total_seconds BIGINT NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS archived_channel_totals (
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            total_seconds BIGINT NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, user_id, channel_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS archived_overlap_totals (
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            other_user_id TEXT NOT NULL,
            total_seconds BIGINT NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, user_id, other_user_id)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def get_open_sessions(guild_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, channel_id FROM voice_sessions
        WHERE guild_id = %s AND leave_at IS NULL
    """, (str(guild_id),))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows