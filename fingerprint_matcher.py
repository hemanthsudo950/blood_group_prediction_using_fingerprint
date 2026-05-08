"""
Advanced Fingerprint Matching Engine
- Multiple algorithms (ORB, SIFT, SURF)
- Image quality assessment
- Confidence scoring
- Weighted matching
"""

import cv2
import numpy as np
import sqlite3
import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple

@dataclass
class MatchResult:
    person_id: int
    name: str
    blood_group: str
    confidence: float
    orb_score: float
    sift_score: float
    surf_score: float
    quality_score: float
    algorithm_weights: Dict[str, float]

@dataclass
class ImageQuality:
    is_valid: bool
    laplacian_variance: float
    brightness: float
    contrast: float
    quality_score: float
    warnings: List[str]


class AdvancedFingerprintMatcher:
    def __init__(self, db_path: str = "fingerprints.db"):
        self.db_path = db_path
        self.min_quality_score = 0.6
        
        # Initialize algorithms
        self.orb = cv2.ORB_create(nfeatures=5000)
        try:
            self.sift = cv2.SIFT_create()
        except AttributeError:
            self.sift = None
            
        try:
            self.surf = cv2.xfeatures2d.SURF_create()
        except:
            self.surf = None
    
    def assess_image_quality(self, image_path: str) -> ImageQuality:
        """
        Assess fingerprint image quality
        Returns quality metrics and warnings
        """
        img = cv2.imread(image_path, 0)
        if img is None:
            return ImageQuality(
                is_valid=False,
                laplacian_variance=0,
                brightness=0,
                contrast=0,
                quality_score=0,
                warnings=["Cannot read the photo. Please try a different image"]
            )
        
        warnings = []
        
        # Check dimensions
        h, w = img.shape
        if h < 100 or w < 100:
            warnings.append("Photo is too small. Use a larger fingerprint image")
        
        # Calculate Laplacian variance (blur detection)
        laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
        if laplacian_var < 100:
            warnings.append("Image is too blurry")
        
        # Calculate brightness
        brightness = np.mean(img)
        if brightness < 50:
            warnings.append("Image is too dark")
        elif brightness > 200:
            warnings.append("Image is too bright")
        
        # Calculate contrast (standard deviation)
        contrast = np.std(img)
        if contrast < 20:
            warnings.append("Image has low contrast")
        
        # Overall quality score
        blur_score = min(1.0, laplacian_var / 500)
        brightness_score = 1.0 if 50 <= brightness <= 200 else 0.5
        contrast_score = min(1.0, contrast / 80)
        
        quality_score = (blur_score + brightness_score + contrast_score) / 3
        is_valid = quality_score >= self.min_quality_score and laplacian_var > 100
        
        return ImageQuality(
            is_valid=is_valid,
            laplacian_variance=float(laplacian_var),
            brightness=float(brightness),
            contrast=float(contrast),
            quality_score=float(quality_score),
            warnings=warnings
        )
    
    def preprocess_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Preprocess fingerprint image for better matching
        """
        img = cv2.imread(image_path, 0)
        if img is None:
            return None
        
        # Histogram equalization for better contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img = clahe.apply(img)
        
        # Morphological operations to remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        
        return img
    
    def match_orb(self, img1: np.ndarray, img2: np.ndarray) -> Tuple[int, float]:
        """ORB matching algorithm"""
        kp1, des1 = self.orb.detectAndCompute(img1, None)
        kp2, des2 = self.orb.detectAndCompute(img2, None)
        
        if des1 is None or des2 is None:
            return 0, 0.0
        
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)
        
        num_good_matches = len(matches)
        
        # Calculate score based on matches and distance
        if num_good_matches > 0:
            avg_distance = np.mean([m.distance for m in matches[:min(50, num_good_matches)]])
            # Normalize distance score
            distance_score = max(0, 1.0 - (avg_distance / 100.0))
            match_score = (num_good_matches * distance_score) / 100.0
            return num_good_matches, float(min(1.0, match_score))
        
        return 0, 0.0
    
    def match_sift(self, img1: np.ndarray, img2: np.ndarray) -> Tuple[int, float]:
        """SIFT matching algorithm (more accurate but slower)"""
        if self.sift is None:
            return 0, 0.0
        
        kp1, des1 = self.sift.detectAndCompute(img1, None)
        kp2, des2 = self.sift.detectAndCompute(img2, None)
        
        if des1 is None or des2 is None:
            return 0, 0.0
        
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1, des2, k=2)
        
        # Lowe's ratio test
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)
        
        num_good_matches = len(good_matches)
        
        if num_good_matches > 0:
            avg_distance = np.mean([m.distance for m in good_matches[:min(50, num_good_matches)]])
            distance_score = max(0, 1.0 - (avg_distance / 1000.0))
            match_score = (num_good_matches * distance_score) / 100.0
            return num_good_matches, float(min(1.0, match_score))
        
        return 0, 0.0
    
    def match_surf(self, img1: np.ndarray, img2: np.ndarray) -> Tuple[int, float]:
        """SURF matching algorithm"""
        if self.surf is None:
            return 0, 0.0
        
        kp1, des1 = self.surf.detectAndCompute(img1, None)
        kp2, des2 = self.surf.detectAndCompute(img2, None)
        
        if des1 is None or des2 is None:
            return 0, 0.0
        
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1, des2, k=2)
        
        # Lowe's ratio test
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)
        
        num_good_matches = len(good_matches)
        
        if num_good_matches > 0:
            avg_distance = np.mean([m.distance for m in good_matches[:min(50, num_good_matches)]])
            distance_score = max(0, 1.0 - (avg_distance / 1000.0))
            match_score = (num_good_matches * distance_score) / 100.0
            return num_good_matches, float(min(1.0, match_score))
        
        return 0, 0.0
    
    def match_fingerprint(self, upload_path: str, top_n: int = 1) -> Optional[List[MatchResult]]:
        """
        Match fingerprint against database using multiple algorithms
        Returns top N matches with confidence scores
        """
        print(f"🔍 Advanced matching: {upload_path}")
        
        # Assess quality
        quality = self.assess_image_quality(upload_path)
        print(f"📊 Quality Score: {quality.quality_score:.2f}")
        
        if not quality.is_valid:
            print(f"⚠ Quality warnings: {quality.warnings}")
        
        # Preprocess image
        img1 = self.preprocess_image(upload_path)
        if img1 is None:
            print("❌ Cannot preprocess image")
            return None
        
        matches_dict = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT person_id, name, blood_group, fingerprint_path FROM users")
            rows = cur.fetchall()
            conn.close()
        except Exception as e:
            print(f"❌ DB Error: {e}")
            return None
        
        if not rows:
            print("⚠ No fingerprints in database")
            return None
        
        # Match against all fingerprints
        for person_id, name, blood_group, fp_path in rows:
            if not os.path.exists(fp_path):
                continue
            
            img2 = self.preprocess_image(fp_path)
            if img2 is None:
                continue
            
            # Get algorithm scores
            orb_matches, orb_score = self.match_orb(img1, img2)
            sift_matches, sift_score = self.match_sift(img1, img2)
            surf_matches, surf_score = self.match_surf(img1, img2)
            
            print(f"👤 {person_id} ({blood_group}): ORB={orb_score:.2f}, SIFT={sift_score:.2f}, SURF={surf_score:.2f}")
            
            # Weighted combination
            weights = {"orb": 0.4, "sift": 0.35, "surf": 0.25}
            combined_score = (
                orb_score * weights["orb"] +
                sift_score * weights["sift"] +
                surf_score * weights["surf"]
            )
            
            # Factor in quality
            quality_adjusted_score = combined_score * quality.quality_score
            
            matches_dict[person_id] = MatchResult(
                person_id=person_id,
                name=name,
                blood_group=blood_group,
                confidence=quality_adjusted_score,
                orb_score=orb_score,
                sift_score=sift_score,
                surf_score=surf_score,
                quality_score=quality.quality_score,
                algorithm_weights=weights
            )
        
        if not matches_dict:
            return None
        
        # Sort by confidence and return top N
        sorted_matches = sorted(
            matches_dict.values(),
            key=lambda x: x.confidence,
            reverse=True
        )
        
        return sorted_matches[:top_n]
