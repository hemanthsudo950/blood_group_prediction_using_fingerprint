import sqlite3
import os
import cv2
import numpy as np
from datetime import datetime

DB_PATH = "fingerprints.db"
BASE_DATASET = "fingerprint_db"

def assess_quality(image_path: str) -> dict:
    """Assess fingerprint image quality"""
    img = cv2.imread(image_path, 0)
    if img is None:
        return {"quality_score": 0, "laplacian_var": 0, "brightness": 0, "contrast": 0}
    
    laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
    brightness = float(np.mean(img))
    contrast = float(np.std(img))
    
    blur_score = min(1.0, laplacian_var / 500)
    brightness_score = 1.0 if 50 <= brightness <= 200 else 0.5
    contrast_score = min(1.0, contrast / 80)
    quality_score = (blur_score + brightness_score + contrast_score) / 3
    
    return {
        "quality_score": float(quality_score),
        "laplacian_var": float(laplacian_var),
        "brightness": brightness,
        "contrast": contrast
    }

print("📌 Creating advanced database...")

# Remove old DB
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Enhanced schema with quality metrics
cur.execute("""
CREATE TABLE users (
    person_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    blood_group TEXT NOT NULL,
    fingerprint_path TEXT NOT NULL,
    quality_score REAL,
    laplacian_variance REAL,
    brightness REAL,
    contrast REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Statistics table
cur.execute("""
CREATE TABLE stats (
    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    total_users INTEGER,
    total_scans INTEGER,
    avg_accuracy REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Scan history for analytics
cur.execute("""
CREATE TABLE scan_history (
    scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,
    confidence REAL,
    matched BOOLEAN,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(person_id) REFERENCES users(person_id)
)
""")

# Scan folders
record_count = 0
for group in os.listdir(BASE_DATASET):
    group_path = os.path.join(BASE_DATASET, group)

    if not os.path.isdir(group_path):
        continue

    for img in os.listdir(group_path):
        img_path = os.path.join(group_path, img)

        # Name is file name without extension
        name = os.path.splitext(img)[0]
        
        # Assess quality
        quality = assess_quality(img_path)

        cur.execute("""
            INSERT INTO users (name, blood_group, fingerprint_path, quality_score, 
                             laplacian_variance, brightness, contrast)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, group, img_path, quality["quality_score"], 
              quality["laplacian_var"], quality["brightness"], quality["contrast"]))

        print(f"✅ Added: {name:20} | {group:4} | Quality: {quality['quality_score']:.2f}")
        record_count += 1

# Initialize stats
cur.execute("INSERT INTO stats (total_users, total_scans, avg_accuracy) VALUES (?, ?, ?)",
           (record_count, 0, 0.0))

conn.commit()
conn.close()

print(f"\n✅ Database Created Successfully! ({record_count} fingerprints added)")
