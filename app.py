import streamlit as st
import cv2
import pandas as pd
import numpy as np
import time
from datetime import datetime
import threading
import queue
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Import project modules with error handling
try:
    from src.webcam.camera import CameraCapture
    from src.webcam.face_emotion import FaceEmotionDetector
    from src.audio.mic_capture import MicrophoneCapture
    from src.audio.audio_emotion import AudioEmotionAnalyzer
    from src.fusion.fusion_engine import FusionEngine
    from src.logger.session_logger import SessionLogger
    from src.logger.report_generator import ReportGenerator
    from src.fallback.rule_based import FallbackEmotionGenerator
    from src.dashboard.ui_components import *
    from src.dashboard.plots import *
    from src.config import TIMELINE_SECONDS, STRESS_THRESHOLD, ALERT_DURATION
    from src.utils import save_session_data
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please install dependencies: pip install -r requirements.txt")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="EMOTISENSE AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'session_logger' not in st.session_state:
    try:
        st.session_state.session_logger = SessionLogger()
    except NameError:
        st.error("Failed to initialize SessionLogger. Please check imports.")
        st.stop()
if 'camera' not in st.session_state:
    st.session_state.camera = CameraCapture()
if 'face_detector' not in st.session_state:
    st.session_state.face_detector = FaceEmotionDetector()
if 'mic_capture' not in st.session_state:
    st.session_state.mic_capture = MicrophoneCapture()
if 'audio_analyzer' not in st.session_state:
    st.session_state.audio_analyzer = AudioEmotionAnalyzer()
if 'fusion_engine' not in st.session_state:
    st.session_state.fusion_engine = FusionEngine()
if 'fallback_generator' not in st.session_state:
    st.session_state.fallback_generator = FallbackEmotionGenerator()
if 'report_generator' not in st.session_state:
    st.session_state.report_generator = ReportGenerator()
if 'session_active' not in st.session_state:
    st.session_state.session_active = False
if 'simulation_mode' not in st.session_state:
    st.session_state.simulation_mode = False

def main():
    st.title("🧠 EMOTISENSE AI")
    st.markdown("*Multimodal Emotion Recognition using Audio + Face*")
    
    # Sidebar
    with st.sidebar:
        st.header("Controls")
        
        # Session controls
        start_session, stop_session, simulation_mode, manual_screenshot = display_session_controls()
        st.session_state.simulation_mode = simulation_mode
        
        # Handle session controls
        if start_session and not st.session_state.session_active:
            st.session_state.session_active = True
            st.session_state.session_logger.start_session()
            if not simulation_mode:
                camera_started = st.session_state.camera.start()
                if camera_started:
                    st.success("Session started with camera!")
                else:
                    st.warning("Session started - Camera unavailable, using fallback")
            else:
                st.success("Session started in simulation mode!")
            st.rerun()
        
        if stop_session and st.session_state.session_active:
            st.session_state.session_active = False
            session_df = st.session_state.session_logger.stop_session()
            st.session_state.camera.stop()
            
            if not session_df.empty:
                # Save session data
                filepath = save_session_data(session_df, st.session_state.session_logger.session_id)
                st.success(f"Session saved to: {filepath}")
            st.rerun()
        
        # Manual screenshot
        if manual_screenshot and st.session_state.session_active:
            try:
                import pyautogui
                from datetime import datetime
                import os
                
                # Create screenshots directory if it doesn't exist
                screenshot_dir = "outputs/snapshots"
                os.makedirs(screenshot_dir, exist_ok=True)
                
                # Get current metrics
                df = st.session_state.session_logger.get_session_dataframe()
                if not df.empty:
                    latest_metrics = df.iloc[-1].to_dict()
                    stress_score = latest_metrics.get('stress', 0)
                    
                    # Capture screenshot
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"MANUAL_{timestamp}_{stress_score:.2f}.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    
                    screenshot = pyautogui.screenshot()
                    screenshot.save(filepath)
                    
                    # Log screenshot
                    screenshot_data = {
                        'timestamp': datetime.now(),
                        'filepath': filepath,
                        'type': 'MANUAL',
                        'score': stress_score
                    }
                    st.session_state.session_logger.screenshots.append(screenshot_data)
                    
                    st.success(f"Screenshot captured: {filename}")
                else:
                    st.warning("No session data available for screenshot")
            except ImportError:
                st.error("Screenshot feature not available - pyautogui not installed")
            except Exception as e:
                st.error(f"Screenshot failed: {e}")
        
        # Status indicators
        st.subheader("System Status")
        camera_status = "🟢 Active" if (st.session_state.camera.is_active or simulation_mode) and st.session_state.session_active else "🔴 Inactive"
        mic_status = "🟢 Active" if (st.session_state.mic_capture.is_available or simulation_mode) and st.session_state.session_active else "🔴 Inactive"
        fer_status = "🟢 Active" if st.session_state.face_detector.is_available and st.session_state.session_active else "🔴 Inactive"
        
        st.write(f"Camera: {camera_status}")
        st.write(f"Microphone: {mic_status}")
        st.write(f"FER Detection: {fer_status}")
        st.write(f"Mode: {'🎭 Simulation' if simulation_mode else '🎥 Live'}")
        
        # FER reinitialization button
        if st.button("🔄 Reinit Face Detector"):
            from src.webcam.face_emotion import FaceEmotionDetector
            st.session_state.face_detector = FaceEmotionDetector()
            st.success("Face detector reinitialized!")
            st.rerun()    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Live Dashboard", "Session Report", "Screenshots", "Analytics", "About"])
    
    with tab1:
        live_dashboard()
    
    with tab2:
        session_report()
    
    with tab3:
        screenshot_gallery()
    
    with tab4:
        analytics_dashboard()
    
    with tab5:
        display_about_info()
    
    # Auto-refresh only when session is active
    if st.session_state.get('session_active', False):
        time.sleep(3)
        st.rerun()

def live_dashboard():
    """Live dashboard tab"""
    if not st.session_state.session_active:
        st.info("Start a session to begin monitoring emotions.")
        return
    
    # Add refresh button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Process current frame/audio
    if st.session_state.simulation_mode:
        # Simulation mode - use fallback generator
        face_emotions = st.session_state.fallback_generator.generate_face_emotions()
        audio_stress_score = st.session_state.fallback_generator.generate_audio_stress()
        frame = None
        st.info("🎭 Simulation Mode Active - Generating synthetic emotions")
    else:
        # Live mode - try to use camera and FER
        if not st.session_state.camera.is_active:
            st.session_state.camera.start()
        
        frame = st.session_state.camera.get_frame()
        
        if frame is not None and st.session_state.face_detector.is_available:
            # Use real FER detection
            emotion_result = st.session_state.face_detector.detect_emotions(frame)
            if isinstance(emotion_result, dict) and 'probs' in emotion_result:
                face_emotions = emotion_result['probs']
                frame = st.session_state.face_detector.draw_emotion_box(frame, emotion_result)
                st.success("🎥 Live FER Detection Active")
            else:
                # Fallback if old format returned
                face_emotions = st.session_state.fallback_generator.generate_face_emotions()
                st.warning("📹 FER format issue - Using dynamic fallback")
        elif frame is not None:
            # Camera works but FER failed
            face_emotions = st.session_state.fallback_generator.generate_face_emotions()
            st.warning("📹 Camera active but FER unavailable - Using dynamic fallback")
        else:
            # No camera frame
            face_emotions = st.session_state.fallback_generator.generate_face_emotions()
            st.error("📷 Camera unavailable - Using dynamic fallback")
        
        # Capture audio
        audio_data = st.session_state.mic_capture.capture_audio_chunk()
        audio_stress_score = st.session_state.audio_analyzer.analyze_stress(audio_data)
    
    # Fuse emotions
    fused_metrics = st.session_state.fusion_engine.fuse_emotions(face_emotions, audio_stress_score)
    
    # Check for automatic screenshot triggers
    if not st.session_state.simulation_mode:  # Only in live mode
        try:
            import pyautogui
            
            # Initialize screenshot counters if not exist
            if 'stress_counter' not in st.session_state:
                st.session_state.stress_counter = 0
            if 'distraction_counter' not in st.session_state:
                st.session_state.distraction_counter = 0
            if 'last_screenshot_time' not in st.session_state:
                st.session_state.last_screenshot_time = {}
            
            current_time = time.time()
            screenshot_taken = False
            
            # EXTREME STRESS: stress >= 0.85 for 3+ seconds
            if fused_metrics['stress'] >= 0.85:
                st.session_state.stress_counter += 1
                if st.session_state.stress_counter >= 3:
                    last_stress_shot = st.session_state.last_screenshot_time.get('STRESS', 0)
                    if current_time - last_stress_shot >= 10:  # 10 second cooldown
                        screenshot_taken = True
                        st.session_state.last_screenshot_time['STRESS'] = current_time
                        st.session_state.stress_counter = 0
            else:
                st.session_state.stress_counter = 0
            
            # EXTREME HAPPINESS: happy emotion + confidence >= 0.75
            dominant_emotion = max(face_emotions, key=face_emotions.get) if face_emotions else None
            if (dominant_emotion == 'happy' and fused_metrics.get('confidence', 0) >= 0.75):
                last_happy_shot = st.session_state.last_screenshot_time.get('HAPPY', 0)
                if current_time - last_happy_shot >= 10:
                    screenshot_taken = True
                    st.session_state.last_screenshot_time['HAPPY'] = current_time
            
            # DISTRACTION: engagement <= 0.10 for 5+ seconds
            if fused_metrics.get('engagement', 1) <= 0.10:
                st.session_state.distraction_counter += 1
                if st.session_state.distraction_counter >= 5:
                    last_distraction_shot = st.session_state.last_screenshot_time.get('DISTRACTION', 0)
                    if current_time - last_distraction_shot >= 10:
                        screenshot_taken = True
                        st.session_state.last_screenshot_time['DISTRACTION'] = current_time
                        st.session_state.distraction_counter = 0
            else:
                st.session_state.distraction_counter = 0
            
            # Take screenshot if triggered
            if screenshot_taken:
                screenshot_dir = "outputs/snapshots"
                os.makedirs(screenshot_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # Determine event type and score
                if st.session_state.stress_counter == 0 and fused_metrics['stress'] >= 0.85:
                    event_type = 'STRESS'
                    score = fused_metrics['stress']
                elif dominant_emotion == 'happy' and fused_metrics.get('confidence', 0) >= 0.75:
                    event_type = 'HAPPY'
                    score = fused_metrics['confidence']
                elif st.session_state.distraction_counter == 0 and fused_metrics.get('engagement', 1) <= 0.10:
                    event_type = 'DISTRACTION'
                    score = fused_metrics['engagement']
                else:
                    event_type = 'AUTO'
                    score = fused_metrics['stress']
                
                filename = f"{event_type}_{timestamp}_{score:.2f}.png"
                filepath = os.path.join(screenshot_dir, filename)
                
                screenshot = pyautogui.screenshot()
                screenshot.save(filepath)
                
                # Log screenshot
                screenshot_data = {
                    'timestamp': datetime.now(),
                    'filepath': filepath,
                    'type': event_type,
                    'score': score
                }
                st.session_state.session_logger.screenshots.append(screenshot_data)
                
                st.success(f"📸 Auto-screenshot: {event_type} detected!")
                
        except ImportError:
            pass  # pyautogui not available
        except Exception as e:
            print(f"Auto-screenshot error: {e}")
    
    # Log data
    st.session_state.session_logger.log_data(face_emotions, audio_stress_score, fused_metrics)
    
    # Get current session data
    df = st.session_state.session_logger.get_session_dataframe()
    
    # Show current timestamp
    st.write(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")
    
    # Display video feed
    if frame is not None:
        st.image(frame, channels="BGR", caption="Live Video Feed")
    else:
        st.info("Video feed not available - using simulation mode")
    
    # Display metrics
    display_metrics_cards(fused_metrics)
    
    # Show audio level indicator
    if not st.session_state.simulation_mode:
        audio_level = np.sqrt(np.mean(audio_data**2)) if 'audio_data' in locals() else 0
        st.progress(min(audio_level * 10, 1.0), text=f"🎤 Audio Level: {audio_level:.3f}")
    
    # Display dominant state
    display_dominant_state(fused_metrics['dominant_state'])
    
    # Check for stress alert
    if len(df) > 0:
        stress_history = df['stress'].tolist()
        display_stress_alert(stress_history, STRESS_THRESHOLD, ALERT_DURATION)
    
    # Initialize chart containers in session state
    if 'pie_chart_container' not in st.session_state:
        st.session_state.pie_chart_container = None
    
    # Display charts
    if len(df) > 0:
        st.plotly_chart(create_timeline_chart(df, TIMELINE_SECONDS), use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_stress_gauge(fused_metrics['stress']), use_container_width=True)
    
    with col2:
        if face_emotions and isinstance(face_emotions, dict):
            # Create fresh chart each time
            pie_chart = create_emotion_pie_chart(face_emotions)
            # Use st.empty() to force refresh
            pie_placeholder = st.empty()
            pie_placeholder.plotly_chart(pie_chart, use_container_width=True)
        else:
            st.error("Invalid emotion data for pie chart")
    
    # Display current emotion data
    display_emotion_breakdown(face_emotions)
    
    # Show audio analysis details
    if not st.session_state.simulation_mode and 'audio_data' in locals():
        st.subheader("🎤 Audio Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Audio Stress Score", f"{audio_stress_score:.3f}")
        with col2:
            rms_energy = np.sqrt(np.mean(audio_data**2))
            st.metric("RMS Energy", f"{rms_energy:.4f}")

def session_report():
    """Session report tab"""
    st.header("Session Report")
    
    # Get current session data
    df = st.session_state.session_logger.get_session_dataframe()
    session_stats = st.session_state.session_logger.get_session_stats()
    
    if df.empty:
        st.info("No session data available. Start a session to generate reports.")
        return
    
    # Display session statistics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Session Statistics")
        st.write(f"**Session ID:** {session_stats['session_id']}")
        st.write(f"**Duration:** {session_stats['duration']}")
        st.write(f"**Total Records:** {session_stats['total_records']}")
        st.write(f"**Average Stress:** {session_stats['avg_stress']:.3f}")
        st.write(f"**Average Engagement:** {session_stats['avg_engagement']:.3f}")
    
    with col2:
        st.subheader("Dominant States")
        if session_stats['dominant_states']:
            for state, count in session_stats['dominant_states'].items():
                st.write(f"**{state.title()}:** {count} times")
    
    # Charts
    st.subheader("Session Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        timeline_chart = create_timeline_chart(df, len(df))
        st.plotly_chart(timeline_chart, use_container_width=True)
    
    with col2:
        summary_chart = create_session_summary_chart(df)
        st.plotly_chart(summary_chart, use_container_width=True)
    
    # Data table
    st.subheader("Raw Data")
    st.dataframe(df, use_container_width=True)
    
    # Export options
    st.subheader("Export Options")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download CSV Report"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"emotion_report_{session_stats['session_id']}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("Generate PDF Report"):
            try:
                pdf_path = st.session_state.report_generator.generate_pdf_report(session_stats, df)
                if pdf_path:
                    st.success(f"PDF report generated: {pdf_path}")
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="Download PDF",
                            data=pdf_file.read(),
                            file_name=f"emotion_report_{session_stats['session_id']}.pdf",
                            mime="application/pdf"
                        )
            except Exception as e:
                st.error(f"Error generating PDF: {e}")

def screenshot_gallery():
    """Screenshot gallery tab"""
    st.header("📸 Screenshot Gallery")
    
    screenshots = st.session_state.session_logger.screenshots
    display_screenshot_gallery(screenshots)

def analytics_dashboard():
    """Analytics dashboard tab"""
    st.header("📊 Advanced Analytics")
    
    df = st.session_state.session_logger.get_session_dataframe()
    session_stats = st.session_state.session_logger.get_session_stats()
    
    if df.empty:
        st.info("No session data available for analytics.")
        return
    
    display_session_analytics(session_stats)
    display_critical_moments(session_stats)
    display_session_feedback(session_stats)
    display_session_comparison(df)

if __name__ == "__main__":
    main()