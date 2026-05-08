"""
Configuration file for BloodSense Advanced
Customize these settings for your deployment
"""

# ============================================
# DATABASE
# ============================================
DB_PATH = "fingerprints.db"
FINGERPRINT_DB_PATH = "fingerprint_db"

# ============================================
# MATCHING SETTINGS
# ============================================

# Minimum quality score (0-1) to accept image
MIN_QUALITY_SCORE = 0.6

# Minimum confidence (0-1) to accept match
MIN_CONFIDENCE_THRESHOLD = 0.4

# Number of top matches to return
TOP_N_MATCHES = 3

# ============================================
# ALGORITHM WEIGHTS
# ============================================
# Adjust weights to prioritize certain algorithms
# Must sum to 1.0 (100%)

ALGORITHM_WEIGHTS = {
    "sift": 0.35,   # Most accurate but slower
    "surf": 0.25,   # Balanced speed/accuracy
    "orb": 0.40     # Fastest, practical for real-time
}

# ============================================
# QUALITY ASSESSMENT THRESHOLDS
# ============================================

# Laplacian variance thresholds (blur detection)
LAPLACIAN_BLURRY_THRESHOLD = 100
LAPLACIAN_GOOD_THRESHOLD = 500

# Brightness thresholds (0-255)
BRIGHTNESS_MIN = 50
BRIGHTNESS_MAX = 200

# Contrast thresholds (standard deviation)
CONTRAST_MIN = 20
CONTRAST_OPTIMAL = 80

# ============================================
# FLASK SETTINGS
# ============================================
DEBUG_MODE = True
HOST = "0.0.0.0"
PORT = 5000

# ============================================
# UPLOAD SETTINGS
# ============================================
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'bmp', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# ============================================
# PREPROCESSING SETTINGS
# ============================================

# CLAHE (Contrast Limited Adaptive Histogram Equalization)
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID_SIZE = (8, 8)

# Morphological operations
MORPH_KERNEL_SIZE = (3, 3)

# ============================================
# QUALITY SCORE CALCULATION
# ============================================

# Weights for quality score (must sum to 1.0)
QUALITY_WEIGHTS = {
    "blur": 0.35,
    "brightness": 0.30,
    "contrast": 0.35
}

# ============================================
# LOGGING
# ============================================
LOG_LEVEL = "INFO"
LOG_FILE = "bloodsense.log"

# ============================================
# ANALYTICS
# ============================================

# Scan history limit
SCAN_HISTORY_LIMIT = 1000

# Stats update interval (seconds)
STATS_UPDATE_INTERVAL = 1

# ============================================
# SECURITY
# ============================================

# Enable CORS for API access from different origins
ENABLE_CORS = False

# Session timeout (minutes)
SESSION_TIMEOUT = 60

# ============================================
# FEATURE FLAGS
# ============================================

ENABLE_SIFT = True
ENABLE_SURF = True
ENABLE_ORB = True
ENABLE_ANALYTICS = True
ENABLE_SCAN_HISTORY = True
ENABLE_QUALITY_ASSESSMENT = True

print("✅ Configuration loaded successfully")
