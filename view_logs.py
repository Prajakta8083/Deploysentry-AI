import sqlite3

conn = sqlite3.connect("audit_logs.db")
cursor = conn.cursor()

cursor.execute("""
SELECT
    timestamp,
    branch,
    files_changed,
    decision,
    matched_rules,
    explanation
FROM audit_logs
""")

rows = cursor.fetchall()

print("\n=================== DEPLOYMENT AUDIT LOG ===================\n")

print(f"{'Time':20} {'Branch':20} {'Files':6} {'Status':10} {'Matched Rule':25}")
print("-" * 90)

for row in rows:
    print(
        f"{row[0]:20} "
        f"{row[1]:20} "
        f"{row[2]:<6} "
        f"{row[3]:10} "
        f"{row[4]:25}"
    )

print("-" * 90)

print("\nDetailed Explanations\n")

for i, row in enumerate(rows, start=1):
    print(f"{i}. {row[0]}")
    print(f"   Branch : {row[1]}")
    print(f"   Status : {row[3]}")
    print(f"   Rule   : {row[4]}")
    print(f"   Reason : {row[5]}")
    print()

conn.close()