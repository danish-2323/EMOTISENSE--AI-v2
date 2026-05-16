import os
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import tempfile
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from src.config import REPORTS_DIR
from src.utils import ensure_directories

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        ensure_directories()
    
    def generate_pdf_report(self, session_stats, df):
        """Generate PDF report for session"""
        if df.empty:
            return None
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"emotion_report_{session_stats['session_id']}_{timestamp}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph("EMOTISENSE AI - Session Report", title_style))
        story.append(Spacer(1, 20))
        
        # Session Information
        story.append(Paragraph("Session Information", self.styles['Heading2']))
        session_info = [
            ['Session ID', session_stats['session_id']],
            ['Start Time', session_stats['start_time'].strftime("%Y-%m-%d %H:%M:%S")],
            ['Duration', str(session_stats['duration']).split('.')[0]],
            ['Total Records', str(session_stats['total_records'])]
        ]
        
        session_table = Table(session_info, colWidths=[2*inch, 3*inch])
        session_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(session_table)
        story.append(Spacer(1, 20))
        
        # Detailed Time Analysis
        story.append(Paragraph("Detailed Time Analysis", self.styles['Heading2']))
        time_analysis = self._analyze_emotion_times(df)
        
        for analysis in time_analysis:
            story.append(Paragraph(analysis, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Key Metrics
        story.append(Paragraph("Key Metrics", self.styles['Heading2']))
        metrics_data = [
            ['Metric', 'Average', 'Maximum', 'Peak Time'],
            ['Stress Level', f"{session_stats['avg_stress']:.3f}", f"{session_stats['max_stress']:.3f}", self._get_peak_time(df, 'stress')],
            ['Engagement', f"{session_stats['avg_engagement']:.3f}", f"{df['engagement'].max():.3f}", self._get_peak_time(df, 'engagement')],
            ['Confidence', f"{session_stats['avg_confidence']:.3f}", f"{df['confidence'].max():.3f}", self._get_peak_time(df, 'confidence')]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 20))
        
        # Add charts
        try:
            story.append(Paragraph("Emotion Timeline Chart", self.styles['Heading2']))
            timeline_chart_path = self._create_timeline_chart(df)
            if timeline_chart_path and os.path.exists(timeline_chart_path):
                story.append(Image(timeline_chart_path, width=6*inch, height=3*inch))
            else:
                story.append(Paragraph("Timeline chart could not be generated.", self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            story.append(Paragraph("Emotion Distribution", self.styles['Heading2']))
            emotion_chart_path = self._create_emotion_distribution_chart(df)
            if emotion_chart_path and os.path.exists(emotion_chart_path):
                story.append(Image(emotion_chart_path, width=6*inch, height=3*inch))
            else:
                story.append(Paragraph("Emotion distribution chart could not be generated.", self.styles['Normal']))
            story.append(Spacer(1, 20))
        except Exception as e:
            print(f"Chart generation error: {e}")
            story.append(Paragraph("Charts could not be generated due to technical issues.", self.styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Dominant States
        if session_stats['dominant_states']:
            story.append(Paragraph("Dominant Emotional States", self.styles['Heading2']))
            states_text = ", ".join([f"{state}: {count} times" for state, count in session_stats['dominant_states'].items()])
            story.append(Paragraph(states_text, self.styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Recommendations
        story.append(Paragraph("Recommendations", self.styles['Heading2']))
        recommendations = self._generate_recommendations(session_stats)
        for rec in recommendations:
            story.append(Paragraph(f"• {rec}", self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return filepath
    
    def _analyze_emotion_times(self, df):
        """Analyze when different emotions were most prominent"""
        analysis = []
        
        if 'stress' in df.columns:
            high_stress_times = df[df['stress'] > 0.7]
            if not high_stress_times.empty:
                start_time = high_stress_times['timestamp'].iloc[0].strftime('%H:%M:%S')
                duration = len(high_stress_times)
                analysis.append(f"<b>High Stress Period:</b> Started at {start_time}, lasted {duration} seconds")
        
        if 'happy' in df.columns:
            happy_times = df[df['happy'] > 0.5]
            if not happy_times.empty:
                start_time = happy_times['timestamp'].iloc[0].strftime('%H:%M:%S')
                duration = len(happy_times)
                analysis.append(f"<b>Happy Period:</b> Started at {start_time}, lasted {duration} seconds")
        
        if 'sad' in df.columns:
            sad_times = df[df['sad'] > 0.4]
            if not sad_times.empty:
                start_time = sad_times['timestamp'].iloc[0].strftime('%H:%M:%S')
                duration = len(sad_times)
                analysis.append(f"<b>Sad Period:</b> Started at {start_time}, lasted {duration} seconds")
        
        if 'angry' in df.columns:
            angry_times = df[df['angry'] > 0.4]
            if not angry_times.empty:
                start_time = angry_times['timestamp'].iloc[0].strftime('%H:%M:%S')
                duration = len(angry_times)
                analysis.append(f"<b>Angry Period:</b> Started at {start_time}, lasted {duration} seconds")
        
        if not analysis:
            analysis.append("No significant emotion periods detected.")
        
        return analysis
    
    def _get_peak_time(self, df, column):
        """Get the time when a metric reached its peak"""
        if column in df.columns and not df.empty:
            peak_idx = df[column].idxmax()
            return df.loc[peak_idx, 'timestamp'].strftime('%H:%M:%S')
        return "N/A"
    
    def _create_timeline_chart(self, df):
        """Create timeline chart and save as image"""
        try:
            plt.figure(figsize=(10, 6))
            
            if 'stress' in df.columns:
                plt.plot(df['timestamp'], df['stress'], 'r-', linewidth=2, label='Stress')
            
            if 'engagement' in df.columns:
                plt.plot(df['timestamp'], df['engagement'], 'g-', linewidth=2, label='Engagement')
            
            plt.title('Emotion Timeline', fontsize=16)
            plt.xlabel('Time', fontsize=12)
            plt.ylabel('Score', fontsize=12)
            plt.ylim(0, 1)
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save as image
            temp_path = os.path.join(tempfile.gettempdir(), f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            plt.savefig(temp_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Timeline chart saved to: {temp_path}")
            return temp_path if os.path.exists(temp_path) else None
        except Exception as e:
            print(f"Timeline chart creation error: {e}")
            return None
    
    def _create_emotion_distribution_chart(self, df):
        """Create emotion distribution chart"""
        try:
            emotions = ['happy', 'sad', 'angry', 'fear', 'surprise', 'neutral']
            avg_emotions = {}
            
            for emotion in emotions:
                if emotion in df.columns:
                    avg_emotions[emotion] = df[emotion].mean()
            
            if avg_emotions:
                plt.figure(figsize=(10, 6))
                colors_list = ['gold', 'blue', 'red', 'purple', 'orange', 'gray']
                
                plt.bar(list(avg_emotions.keys()), list(avg_emotions.values()), 
                       color=colors_list[:len(avg_emotions)])
                
                plt.title('Average Emotion Distribution', fontsize=16)
                plt.xlabel('Emotions', fontsize=12)
                plt.ylabel('Average Score', fontsize=12)
                plt.ylim(0, max(avg_emotions.values()) * 1.1)
                plt.tight_layout()
                
                temp_path = os.path.join(tempfile.gettempdir(), f"emotions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                plt.savefig(temp_path, dpi=150, bbox_inches='tight')
                plt.close()
                
                print(f"Emotion chart saved to: {temp_path}")
                return temp_path if os.path.exists(temp_path) else None
            else:
                print("No emotion data found for chart")
                return None
        except Exception as e:
            print(f"Emotion chart creation error: {e}")
            return None
    
    def _generate_recommendations(self, stats):
        """Generate recommendations based on session statistics"""
        recommendations = []
        
        if stats['avg_stress'] > 0.7:
            recommendations.append("High stress levels detected. Consider stress management techniques.")
        elif stats['avg_stress'] < 0.3:
            recommendations.append("Low stress levels indicate good emotional regulation.")
        
        if stats['avg_engagement'] < 0.4:
            recommendations.append("Low engagement detected. Consider more interactive activities.")
        elif stats['avg_engagement'] > 0.7:
            recommendations.append("High engagement levels - excellent focus and attention.")
        
        if stats['avg_confidence'] < 0.5:
            recommendations.append("Confidence levels could be improved through positive reinforcement.")
        
        if not recommendations:
            recommendations.append("Overall emotional state appears balanced and healthy.")
        
        return recommendations