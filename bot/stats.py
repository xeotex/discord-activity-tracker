import time
from database import get_connection
from datetime import datetime, timedelta

def get_total_seconds(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Archivierte Gesamtzeit zusammengefasst (Sessions > 31 Tage)
    cursor.execute("""
        SELECT total_seconds FROM archived_totals
        WHERE user_id = ?
    """, (str(user_id),))
    archived_row = cursor.fetchone()
    archived_total = archived_row["total_seconds"] if archived_row is not None else 0

    # Live-Zeit von beendeten Sessions
    cursor.execute("""
        SELECT SUM(leave_at - join_at) AS total
        FROM voice_sessions
        WHERE user_id = ? AND leave_at IS NOT NULL
    """, (str(user_id),))
    row = cursor.fetchone()
    live_total = row["total"] if row["total"] is not None else 0

    # Berechnen von möglicher Session
    cursor.execute("""
        SELECT join_at FROM voice_sessions
        WHERE user_id = ? AND leave_at IS NULL
        ORDER BY id DESC LIMIT 1
    """, (str(user_id),))
    open_row = cursor.fetchone()
    if open_row is not None:
        live_total += int(time.time()) - open_row["join_at"]

    conn.close()
    return archived_total + live_total

def format_duration(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours}h {minutes}m {secs}s"

def get_total_seconds_since(user_id, since_timestamp):
    conn = get_connection()
    cursor = conn.cursor()
    now = int(time.time())

    cursor.execute("""
        SELECT join_at, leave_at FROM voice_sessions
        WHERE user_id = ?
        AND (leave_at IS NULL OR leave_at > ?)
    """, (str(user_id), since_timestamp))

    rows = cursor.fetchall()
    conn.close()

    total = 0
    for row in rows:
        start = max(row["join_at"], since_timestamp)
        end = row["leave_at"] if row["leave_at"] is not None else now
        if end > start:
            total += end - start

    return total

def start_of_week():
    now = datetime.now()
    monday = now - timedelta(days=now.weekday())
    monday_midnight = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(monday_midnight.timestamp())

def start_of_month():
    now = datetime.now()
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return int(first_of_month.timestamp())

def get_channel_leaderboard(channel_id, since_timestamp=None):
    conn = get_connection()
    cursor = conn.cursor()
    now = int(time.time())

    totals = {}

    if since_timestamp is None:
        cursor.execute("""
            SELECT user_id, total_seconds FROM archived_channel_totals
            WHERE channel_id = ?
        """, (str(channel_id),))
        for row in cursor.fetchall():
            totals[row["user_id"]] = totals.get(row["user_id"], 0) + row["total_seconds"]
        since_timestamp = 0

    cursor.execute("""
        SELECT user_id, join_at, leave_at FROM voice_sessions
        WHERE channel_id = ?
        AND (leave_at IS NULL OR leave_at > ?)
    """, (str(channel_id), since_timestamp))

    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        start = max(row["join_at"], since_timestamp)
        end = row["leave_at"] if row["leave_at"] is not None else now
        if end > start:
            user_id = row["user_id"]
            totals[user_id] = totals.get(user_id, 0) + (end - start)

    return sorted(totals.items(), key=lambda item: item[1], reverse=True)


def get_overlap_leaderboard(user_id, since_timestamp=None):
    conn = get_connection()
    cursor = conn.cursor()
    now = int(time.time())

    totals = {}

    if since_timestamp is None:
        cursor.execute("""
            SELECT other_user_id, total_seconds FROM archived_overlap_totals
            WHERE user_id = ?
        """, (str(user_id),))
        for row in cursor.fetchall():
            totals[row["other_user_id"]] = totals.get(row["other_user_id"], 0) + row["total_seconds"]
        since_timestamp = 0

    cursor.execute("""
        SELECT channel_id, join_at, leave_at FROM voice_sessions
        WHERE user_id = ?
        AND (leave_at IS NULL OR leave_at > ?)
    """, (str(user_id), since_timestamp))
    my_sessions = cursor.fetchall()

    for my_session in my_sessions:
        my_start = max(my_session["join_at"], since_timestamp)
        my_end = my_session["leave_at"] if my_session["leave_at"] is not None else now

        cursor.execute("""
            SELECT user_id, join_at, leave_at FROM voice_sessions
            WHERE channel_id = ?
            AND user_id != ?
            AND (leave_at IS NULL OR leave_at > ?)
            AND join_at < ?
        """, (my_session["channel_id"], str(user_id), my_start, my_end))

        others = cursor.fetchall()

        for other in others:
            other_start = max(other["join_at"], since_timestamp)
            other_end = other["leave_at"] if other["leave_at"] is not None else now

            overlap_start = max(my_start, other_start)
            overlap_end = min(my_end, other_end)

            if overlap_end > overlap_start:
                overlap_seconds = overlap_end - overlap_start
                other_id = other["user_id"]
                totals[other_id] = totals.get(other_id, 0) + overlap_seconds

    conn.close()
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)

def get_server_leaderboard(guild_id, since_timestamp=None):
    conn = get_connection()
    cursor = conn.cursor()
    now = int(time.time())

    totals = {}

    if since_timestamp is None:
        cursor.execute("""
            SELECT user_id, total_seconds FROM archived_totals
            WHERE guild_id = ?
        """, (str(guild_id),))
        for row in cursor.fetchall():
            totals[row["user_id"]] = totals.get(row["user_id"], 0) + row["total_seconds"]
        since_timestamp = 0

    cursor.execute("""
        SELECT user_id, join_at, leave_at FROM voice_sessions
        WHERE guild_id = ?
        AND (leave_at IS NULL OR leave_at > ?)
    """, (str(guild_id), since_timestamp))

    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        start = max(row["join_at"], since_timestamp)
        end = row["leave_at"] if row["leave_at"] is not None else now
        if end > start:
            user_id = row["user_id"]
            totals[user_id] = totals.get(user_id, 0) + (end - start)

    return sorted(totals.items(), key=lambda item: item[1], reverse=True)