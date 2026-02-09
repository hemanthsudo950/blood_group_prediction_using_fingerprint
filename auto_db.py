import sqlite3
import os

DB_PATH = "fingerprints.db"
BASE_DATASET = "fingerprint_db"

print("📌 Creating database...")

# Remove old DB
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE users (
    person_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    blood_group TEXT,
    fingerprint_path TEXT
)
""")

# Scan folders
for group in os.listdir(BASE_DATASET):
    group_path = os.path.join(BASE_DATASET, group)

    if not os.path.isdir(group_path):
        continue

    for img in os.listdir(group_path):
        img_path = os.path.join(group_path, img)

        # Name is file name without extension
        name = os.path.splitext(img)[0]

        cur.execute("""
            INSERT INTO users (name, blood_group, fingerprint_path)
            VALUES (?, ?, ?)
        """, (name, group, img_path))

        print("Added:", name, group, img_path)

conn.commit()
conn.close()

print("✅ Database Created Successfully!")
