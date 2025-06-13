from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import io


class PDFGenerator:
    """Handles PDF generation for therapy session conversations"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup basic PDF styles"""
        self.title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=1,
            textColor=colors.blue
        )
        
        self.client_style = ParagraphStyle(
            'Client',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leftIndent=10,
            backColor=colors.lightgrey
        )
        
        self.therapist_style = ParagraphStyle(
            'Therapist',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leftIndent=10,
            backColor=colors.lightblue
        )
    
    def create_pdf(self, messages, client_name, session_title="Therapy Session"):
        """Create PDF from conversation messages"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Header
        story.append(Paragraph(f"Therapy Session Conversation", self.title_style))
        story.append(Paragraph(f"<b>Client:</b> {client_name}", self.styles['Normal']))
        story.append(Paragraph(f"<b>Session:</b> {session_title}", self.styles['Normal']))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Messages
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "system":
                continue
                
            # Escape HTML and handle line breaks
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
            
            if role == "user":
                story.append(Paragraph(f"<b>{client_name}:</b>", self.styles['Heading3']))
                story.append(Paragraph(content, self.client_style))
            elif role == "assistant":
                story.append(Paragraph("<b>Therapist:</b>", self.styles['Heading3']))
                story.append(Paragraph(content, self.therapist_style))
            
            story.append(Spacer(1, 10))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def create_filename(self, client_name, session_title):
        """Create safe filename"""
        safe_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = "".join(c for c in session_title if c.isalnum() or c in (' ', '-', '_')).strip()
        return f"{safe_name}_{safe_title}_{datetime.now().strftime('%Y%m%d')}.pdf"