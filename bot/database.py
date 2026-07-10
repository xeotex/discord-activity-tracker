import sqlite3

DB_PATH = "voice_stats.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voice_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            join_at INTEGER NOT NULL,
            leave_at INTEGER
        )
    """)
    conn.commit()
    conn.close()

def get_open_sessions(guild_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, channel_id FROM voice_sessions
        WHERE guild_id = ? AND leave_at IS NULL
    """, (str(guild_id),))
    rows = cursor.fetchall()
    conn.close()
    return rows


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voice_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            join_at INTEGER NOT NULL,
            leave_at INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS archived_totals (
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            total_seconds INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS archived_channel_totals (
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            total_seconds INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, user_id, channel_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS archived_overlap_totals (
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            other_user_id TEXT NOT NULL,
            total_seconds INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, user_id, other_user_id)
        )
    """)

    conn.commit()
    conn.close()
