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
        return False, f"Database not found: {DB_PATH}"

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        exists = cur.fetchone()
        conn.close()

        if exists is None:
            return False, "Table 'users' missing in database"

        return True, None
    
    except Exception as e:
        return False, f"DB Error: {e}"

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
        return None

    kp1, des1 = orb.detectAndCompute(img1, None)
    if des1 is None:
        print("⚠ No features in uploaded fingerprint")
        return None

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
        return None

    if not rows:
        return None

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
    return best_match_id

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
        return jsonify({"error": "Upload field name must be 'fingerprint'"}), 400

    file = request.files["fingerprint"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    print("💾 Saved to:", save_path)

    person_id = match_fingerprint(save_path)
    if not person_id:
        return jsonify({"error": "Fingerprint not recognized"}), 404

    # Fetch details
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name, blood_group FROM users WHERE person_id=?", (person_id,))
        row = cur.fetchone()
        conn.close()
    except Exception as e:
        print("❌ DB Fetch Error:", e)
        return jsonify({"error": "DB error"}), 500

    if not row:
        return jsonify({"error": "User not found in DB"}), 500

    return jsonify({
        "name": row[0],
        "blood_group": row[1]
    })

# --------------------------------------------------------
# RUN
# --------------------------------------------------------
if __name__ == "__main__":   # FIXED
    app.run(debug=True)
