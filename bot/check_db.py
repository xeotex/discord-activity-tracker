from database import get_connection

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM voice_sessions ORDER BY id DESC")
rows = cursor.fetchall()

for row in rows:
    print(row)

cursor.close()
conn.close()