from database import get_connection

conn = get_connection()
cursor = conn.cursor()

print("=== archived_totals ===")
cursor.execute("SELECT * FROM archived_totals")
for row in cursor.fetchall():
    print(dict(row))

print("\n=== archived_channel_totals ===")
cursor.execute("SELECT * FROM archived_channel_totals")
for row in cursor.fetchall():
    print(dict(row))

print("\n=== archived_overlap_totals ===")
cursor.execute("SELECT * FROM archived_overlap_totals")
for row in cursor.fetchall():
    print(dict(row))

conn.close()