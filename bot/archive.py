import time
from database import get_connection

ARCHIVE_AFTER_DAYS = 31

def archive_old_sessions():
    conn = get_connection()
    cursor = conn.cursor()
    now = int(time.time())
    cutoff = now - ARCHIVE_AFTER_DAYS * 86400

    cursor.execute("""
        SELECT id, guild_id, user_id, channel_id, join_at, leave_at
        FROM voice_sessions
        WHERE leave_at IS NOT NULL AND leave_at < ?
    """, (cutoff,))
    old_sessions = cursor.fetchall()

    if not old_sessions:
        conn.close()
        return 0

    # Gesamtzeit pro User & pro User+Channel aufsummiert
    user_totals = {}
    channel_totals = {}

    for s in old_sessions:
        duration = s["leave_at"] - s["join_at"]

        key_user = (s["guild_id"], s["user_id"])
        user_totals[key_user] = user_totals.get(key_user, 0) + duration

        key_channel = (s["guild_id"], s["user_id"], s["channel_id"])
        channel_totals[key_channel] = channel_totals.get(key_channel, 0) + duration

    for (guild_id, user_id), seconds in user_totals.items():
        cursor.execute("""
            INSERT INTO archived_totals (guild_id, user_id, total_seconds)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id)
            DO UPDATE SET total_seconds = total_seconds + excluded.total_seconds
        """, (guild_id, user_id, seconds))

    for (guild_id, user_id, channel_id), seconds in channel_totals.items():
        cursor.execute("""
            INSERT INTO archived_channel_totals (guild_id, user_id, channel_id, total_seconds)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id, channel_id)
            DO UPDATE SET total_seconds = total_seconds + excluded.total_seconds
        """, (guild_id, user_id, channel_id, seconds))

    # Berechnung von Überschneidungen zwischen den zu archivierenden Sessions 
    overlap_totals = {}
    sessions_list = list(old_sessions)

    for i in range(len(sessions_list)):
        a = sessions_list[i]
        for j in range(i + 1, len(sessions_list)):
            b = sessions_list[j]
            if a["channel_id"] != b["channel_id"] or a["user_id"] == b["user_id"]:
                continue

            overlap_start = max(a["join_at"], b["join_at"])
            overlap_end = min(a["leave_at"], b["leave_at"])

            if overlap_end > overlap_start:
                overlap = overlap_end - overlap_start
                guild_id = a["guild_id"]
                key_ab = (guild_id, a["user_id"], b["user_id"])
                key_ba = (guild_id, b["user_id"], a["user_id"])
                overlap_totals[key_ab] = overlap_totals.get(key_ab, 0) + overlap
                overlap_totals[key_ba] = overlap_totals.get(key_ba, 0) + overlap

    for (guild_id, user_id, other_user_id), seconds in overlap_totals.items():
        cursor.execute("""
            INSERT INTO archived_overlap_totals (guild_id, user_id, other_user_id, total_seconds)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id, other_user_id)
            DO UPDATE SET total_seconds = total_seconds + excluded.total_seconds
        """, (guild_id, user_id, other_user_id, seconds))

    ids = [s["id"] for s in old_sessions]
    cursor.executemany("DELETE FROM voice_sessions WHERE id = ?", [(i,) for i in ids])

    conn.commit()
    conn.close()
    return len(old_sessions)