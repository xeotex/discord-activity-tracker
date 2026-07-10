import time
from database import get_connection
from database import get_connection, get_open_sessions

def start_session(guild_id, user_id, channel_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO voice_sessions (guild_id, user_id, channel_id, join_at)
        VALUES (?, ?, ?, ?)
    """, (str(guild_id), str(user_id), str(channel_id), int(time.time())))
    conn.commit()
    conn.close()

def end_open_session(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM voice_sessions
        WHERE user_id = ? AND leave_at IS NULL
        ORDER BY id DESC LIMIT 1
    """, (str(user_id),))
    row = cursor.fetchone()

    if row is not None:
        cursor.execute("""
            UPDATE voice_sessions
            SET leave_at = ?
            WHERE id = ?
        """, (int(time.time()), row["id"]))
        conn.commit()
        conn.close()

def close_session_by_id(session_id, leave_at):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE voice_sessions
        SET leave_at = ?
        WHERE id = ?
    """, (leave_at, session_id))
    conn.commit()
    conn.close()        

import time

def reconcile_sessions(guild):
    now = int(time.time())
    open_sessions = get_open_sessions(guild.id)

    # Voice Channel check mit user_id -> channel_id
    currently_connected = {}
    for channel in guild.voice_channels:
        for member in channel.members:
            currently_connected[str(member.id)] = str(channel.id)

    handled_users = set()

    for session in open_sessions:
        user_id = session["user_id"]
        db_channel = session["channel_id"]
        handled_users.add(user_id)

        actual_channel = currently_connected.get(user_id)

        if actual_channel is None:
            # Alte Session am Neustart-Zeitpunkt abschließen wenn User weg ist
            close_session_by_id(session["id"], now)
        elif actual_channel != db_channel:
           
            close_session_by_id(session["id"], now)
            start_session(guild.id, user_id, actual_channel)

    for user_id, channel_id in currently_connected.items():
        if user_id not in handled_users:
            start_session(guild.id, user_id, channel_id)    

    