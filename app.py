from flask import Flask, render_template, send_from_directory, request, jsonify
from werkzeug.utils import secure_filename
import os
import cv2
import sqlite3
import traceback

app = Flask(__name__)   # FIXED

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_PATH = "fingerprints.db"

# --------------------------------------------------------
# CHECK DATABASE IS OK
# --------------------------------------------------------
def check_database_ok():
    if not os.path.exists(DB_PATH):
        return False, "Database not found. Please set up the database first"

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        exists = cur.fetchone()
        conn.close()

        if exists is None:
            return False, "Database is not properly set up. Please run setup first"

        return True, None
    
    except Exception as e:
        return False, f"Database error: {e}"

# --------------------------------------------------------
# FINGERPRINT MATCHING USING ORB
# --------------------------------------------------------
def match_fingerprint(upload_path):
    print("🔍 Matching fingerprint:", upload_path)

    orb = cv2.ORB_create()
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    img1 = cv2.imread(upload_path, 0)
    if img1 is None:
        print("⚠ Cannot read uploaded fingerprint")
        return None, 0

    kp1, des1 = orb.detectAndCompute(img1, None)
    if des1 is None:
        print("⚠ No features in uploaded fingerprint")
        return None, 0

    best_match_id = None
    best_score = 0

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT person_id, fingerprint_path FROM users")
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        print("❌ Failed to load fingerprints:", e)
        traceback.print_exc()
        return None, 0

    if not rows:
        return None, 0

    for person_id, fp_path in rows:
        if not os.path.exists(fp_path):
            print("❌ Missing file:", fp_path)
            continue

        img2 = cv2.imread(fp_path, 0)
        if img2 is None:
            continue

        kp2, des2 = orb.detectAndCompute(img2, None)
        if des2 is None:
            continue

        matches = bf.match(des1, des2)
        score = len(matches)

        print(f"Score with ID {person_id}: {score}")

        if score > best_score:
            best_score = score
            best_match_id = person_id

    print("🎯 BEST:", best_match_id, "Score:", best_score)
    return best_match_id, best_score

# --------------------------------------------------------
# ROUTES
# --------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')

@app.route("/predict", methods=["POST"])
def predict():
    print("📥 Predict called")

    ok, msg = check_database_ok()
    if not ok:
        return jsonify({"error": msg}), 500

    if "fingerprint" not in request.files:
        return jsonify({"error": "Please upload a fingerprint image"}), 400

    file = request.files["fingerprint"]
    if file.filename == "":
        return jsonify({"error": "Please select a file to scan"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    print("💾 Saved to:", save_path)

    person_id, best_score = match_fingerprint(save_path)
    if not person_id:
        # Insert failed scan
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("INSERT INTO scan_history (person_id, confidence, matched) VALUES (?, ?, ?)",
                       (None, 0.0, False))
            conn.commit()
            conn.close()
        except Exception as e:
            print("❌ Failed to log failed scan:", e)
        return jsonify({"error": "Fingerprint not recognized"}), 404

    # Fetch details
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name, blood_group FROM users WHERE person_id=?", (person_id,))
        row = cur.fetchone()
        
        # Insert successful scan - using score as confidence (normalize to 0-1)
        confidence = min(1.0, best_score / 100.0)
        cur.execute("INSERT INTO scan_history (person_id, confidence, matched) VALUES (?, ?, ?)",
                   (person_id, confidence, True))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print("❌ DB Fetch Error:", e)
        return jsonify({"error": "Something went wrong. Please try again"}), 500

    if not row:
        return jsonify({"error": "Fingerprint matched but user data is missing"}), 500

    return jsonify({
        "name": row[0],
        "blood_group": row[1],
        "confidence": round(confidence, 2)
    })

@app.route("/stats", methods=["GET"])
def get_stats():
    """Get system statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Total scans
        cur.execute('SELECT COUNT(*) FROM scan_history')
        total_scans = cur.fetchone()[0]
        
        # Average accuracy
        cur.execute('SELECT AVG(confidence) FROM scan_history WHERE matched = 1')
        avg_accuracy = cur.fetchone()[0] or 0
        
        # Blood group distribution
        cur.execute('SELECT blood_group, COUNT(*) FROM users GROUP BY blood_group')
        blood_group_dist = dict(cur.fetchall())
        
        # Quality distribution (categorized into high/medium/low)
        cur.execute('''
            SELECT 
                CASE 
                    WHEN quality_score >= 80 THEN 'high'
                    WHEN quality_score >= 50 THEN 'medium'
                    ELSE 'low'
                END as category,
                COUNT(*) as count
            FROM users
            GROUP BY CASE 
                WHEN quality_score >= 80 THEN 'high'
                WHEN quality_score >= 50 THEN 'medium'
                ELSE 'low'
            END
        ''')
        quality_data = cur.fetchall()
        quality_dist = {'high': 0, 'medium': 0, 'low': 0}
        for category, count in quality_data:
            if category:
                quality_dist[category] = count
        
        # Total users
        cur.execute('SELECT COUNT(*) FROM users')
        total_users = cur.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_users': total_users,
            'total_scans': total_scans,
            'avg_accuracy': round(avg_accuracy, 2),
            'blood_group_distribution': blood_group_dist,
            'quality_distribution': quality_dist
        })
    except Exception as e:
        print(f"❌ Stats error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/users", methods=["GET"])
def get_users():
    """Get all registered users"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT person_id, name, blood_group, quality_score FROM users ORDER BY blood_group")
        rows = cur.fetchall()
        conn.close()
        
        users = [
            {
                "id": row[0],
                "name": row[1],
                "blood_group": row[2],
                "quality_score": round(row[3], 2) if row[3] else 0
            }
            for row in rows
        ]
        
        return jsonify(users)
    except Exception as e:
        print(f"❌ Users error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/scan-history", methods=["GET"])
def get_scan_history():
    """Get recent scan history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT h.scan_id, h.person_id, u.name, u.blood_group, h.confidence, h.matched, h.scanned_at
            FROM scan_history h
            JOIN users u ON h.person_id = u.person_id
            ORDER BY h.scanned_at DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        conn.close()
        
        history = [
            {
                "id": row[0],
                "person_id": row[1],
                "name": row[2],
                "blood_group": row[3],
                "confidence": round(row[4], 3) if row[4] else 0,
                "matched": bool(row[5]),
                "timestamp": row[6]
            }
            for row in rows
        ]
        
        return jsonify(history)
    except Exception as e:
        print(f"❌ Scan history error: {e}")
        return jsonify({"error": str(e)}), 500

# --------------------------------------------------------
# RUN
# --------------------------------------------------------
if __name__ == "__main__":   # FIXED
    app.run(debug=True)
