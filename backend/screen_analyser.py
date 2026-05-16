"""
screen_analyser.py
Analyses a screenshot and returns a focus score (0-100) + optional alert.
NO OCR REQUIRED - Uses image analysis and color patterns.
"""

import re
from io import BytesIO
import random

def analyse_screenshot(image_bytes: bytes, study_app: str = '') -> dict:
    """
    Analyses screenshot without OCR.
    Uses image characteristics and randomization to simulate app detection.
    Returns:
        { focus_score: int (0-100), alert: str | None, label: str, detected_app: str }
    """
    try:
        return _analyze_without_ocr(image_bytes, study_app)
    except Exception as e:
        print(f"[SCREEN ERROR] {e}")
        return {"focus_score": 75, "alert": None, "label": "Unknown", "detected_app": study_app}


def _analyze_without_ocr(image_bytes: bytes, study_app: str) -> dict:
    """
    Analyze screenshot using image properties instead of OCR.
    Detects common app patterns by color, layout, and image characteristics.
    """
    try:
        from PIL import Image
        img = Image.open(BytesIO(image_bytes)).convert('RGB')
        
        # Get image statistics
        width, height = img.size
        
        # Sample colors from different regions
        colors = _sample_colors(img)
        avg_brightness = sum(sum(c) for c in colors) / (len(colors) * 3)
        
        # Detect app based on visual patterns
        detected_app, confidence = _detect_app_by_visuals(colors, avg_brightness, study_app)
        
        print(f"[VISUAL] Size: {width}x{height}, Brightness: {avg_brightness:.1f}, Detected: {detected_app}, Confidence: {confidence}")
        
        # Calculate focus score based on detection confidence
        if detected_app.lower() == study_app.lower():
            focus_score = 90 + random.randint(-5, 5)
            return {
                "focus_score": focus_score,
                "alert": None,
                "label": "On Task",
                "detected_app": detected_app,
            }
        
        # Check if it's a known distraction app
        distraction_apps = ['youtube', 'netflix', 'instagram', 'twitter', 'facebook', 
                           'tiktok', 'reddit', 'twitch', 'discord', 'spotify']
        
        if any(dist in detected_app.lower() for dist in distraction_apps):
            return {
                "focus_score": 10,
                "alert": f"🚨 OFF-TASK: You're on {detected_app}! Return to {study_app} NOW!",
                "label": "Distracted",
                "detected_app": detected_app,
            }
        
        # Study-related but wrong app
        study_apps = ['chatgpt', 'claude', 'vscode', 'notion', 'docs', 'github', 'stackoverflow']
        if any(app in detected_app.lower() for app in study_apps):
            return {
                "focus_score": 60,
                "alert": f"⚠️ You should be in {study_app}. Switch back now!",
                "label": "Wrong Study App",
                "detected_app": detected_app,
            }
        
        # Unknown - moderate score
        return {
            "focus_score": 50 + random.randint(-10, 10),
            "alert": f"⚠️ Cannot verify you're in {study_app}",
            "label": "Unclear",
            "detected_app": detected_app,
        }
        
    except Exception as e:
        print(f"[VISUAL ERROR] {e}")
        # Fallback: assume they're on task
        return {
            "focus_score": 75,
            "alert": None,
            "label": "No Analysis",
            "detected_app": study_app,
        }


def _sample_colors(img):
    """Sample colors from 9 regions of the image."""
    width, height = img.size
    colors = []
    
    # Sample from 9 grid positions
    for y_frac in [0.1, 0.5, 0.9]:
        for x_frac in [0.1, 0.5, 0.9]:
            x = int(width * x_frac)
            y = int(height * y_frac)
            try:
                pixel = img.getpixel((x, y))
                colors.append(pixel)
            except:
                pass
    
    return colors if colors else [(128, 128, 128)]


def _detect_app_by_visuals(colors, brightness, study_app):
    """
    Detect app based on visual characteristics.
    This is a heuristic approach without OCR.
    """
    
    # Calculate color characteristics
    avg_r = sum(c[0] for c in colors) / len(colors)
    avg_g = sum(c[1] for c in colors) / len(colors)
    avg_b = sum(c[2] for c in colors) / len(colors)
    
    # Dark theme detection
    is_dark = brightness < 100
    
    # Color-based app detection (rough heuristics)
    
    # YouTube (red theme)
    if avg_r > 150 and avg_r > avg_g + 30 and avg_r > avg_b + 30:
        return "YouTube", 0.7
    
    # Dark coding environment (VSCode, etc.)
    if is_dark and avg_b > avg_r and avg_b > avg_g:
        if 'vscode' in study_app.lower() or 'code' in study_app.lower():
            return study_app, 0.8
        return "VSCode", 0.6
    
    # Light document (Google Docs, Word, etc.)
    if brightness > 200 and abs(avg_r - avg_g) < 20 and abs(avg_g - avg_b) < 20:
        if 'doc' in study_app.lower() or 'word' in study_app.lower():
            return study_app, 0.8
        return "Document Editor", 0.5
    
    # ChatGPT/Claude (typically light with some green/blue)
    if brightness > 150 and (avg_g > avg_r or avg_b > avg_r):
        if 'chatgpt' in study_app.lower() or 'gpt' in study_app.lower():
            return "ChatGPT", 0.8
        if 'claude' in study_app.lower():
            return "Claude", 0.8
        return "AI Chat", 0.5
    
    # Dark theme general (could be many apps)
    if is_dark:
        # Assume they're in their study app if it's dark
        if study_app:
            return study_app, 0.6
        return "Dark App", 0.4
    
    # Default: assume study app with moderate confidence
    if study_app:
        return study_app, 0.6
    
    return "Unknown", 0.3
