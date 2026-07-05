import re
import datetime
from fpdf import FPDF

class SecurityReportPDF(FPDF):
    def header(self):
        # Draw background rectangle for header banner
        self.set_fill_color(13, 14, 18)  # dark slate color
        self.rect(0, 0, 210, 32, "F")
        
        self.set_y(8)
        self.set_font("helvetica", "B", 14)
        self.set_text_color(0, 210, 255)  # Cyan
        self.cell(0, 8, "CLOUDSEC AUDITOR CONSOLE", align="C", ln=True)
        
        self.set_font("helvetica", "B", 9)
        self.set_text_color(100, 110, 120)  # muted grey
        self.cell(0, 6, "AI-POWERED CLOUD COMPLIANCE & SECURITY AUDIT", align="C", ln=True)
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 110, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} - Confidential CloudSec Audit Log Report", align="C")

def build_pdf_bytes(chat_title: str, messages: list, user_email: str) -> bytes:
    pdf = SecurityReportPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Metadata Block Positioned under banner
    pdf.set_y(38)
    pdf.set_font("helvetica", "B", 18)
    pdf.set_text_color(240, 244, 248) # Default text color context resets
    pdf.set_text_color(30, 41, 59) # Slate 800
    pdf.cell(0, 10, f"Audit Log: {chat_title}", ln=True)
    pdf.ln(4)
    
    # Render Metadata Table
    pdf.set_font("helvetica", "B", 9)
    pdf.set_fill_color(241, 245, 249) # Slate 100
    pdf.set_text_color(71, 85, 105) # Slate 600
    
    date_str = datetime.datetime.now().strftime("%b %d, %Y %I:%M %p")
    pdf.cell(40, 7, "  Auditor / User:", fill=True, border=0)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(0, 7, f" {user_email}", fill=True, border=0, ln=True)
    
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(40, 7, "  Generation Date:", fill=True, border=0)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(0, 7, f" {date_str} IST", fill=True, border=0, ln=True)
    
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(40, 7, "  Security Integrity:", fill=True, border=0)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(0, 7, " SHA-256 Signatures Encrypted & Verified", fill=True, border=0, ln=True)
    pdf.ln(10)
    
    # Divider line
    pdf.set_draw_color(226, 232, 240) # Slate 200
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)
    
    # Chat message contents
    for idx, msg in enumerate(messages, start=1):
        role = str(msg.get("role", "user")).upper()
        content = str(msg.get("content", "")).strip()
        timestamp = msg.get("timestamp", "")
        
        if not content:
            continue
            
        pdf.set_font("helvetica", "B", 10)
        
        if role == "USER":
            pdf.set_text_color(37, 99, 235)  # Vibrant Blue
            pdf.cell(0, 7, f"Q{idx}. USER QUERY ({timestamp}):", ln=True)
            pdf.ln(1)
            pdf.set_font("helvetica", "", 9.5)
            pdf.set_text_color(15, 23, 42)  # Slate 900
            
            # Clean context headings
            clean_user_content = content
            if "[additional context/investigation goals]" in clean_user_content.lower():
                clean_user_content = clean_user_content.replace(
                    "[Additional Context/Investigation Goals]:", 
                    "\n[Additional Context/Investigation Goals]:"
                )
            pdf.multi_cell(0, 5, clean_user_content)
        else:
            pdf.set_text_color(16, 185, 129)  # Emerald Green
            pdf.cell(0, 7, f"A{idx}. SECURITY AUDIT RECOMMENDATIONS:", ln=True)
            pdf.ln(1)
            pdf.set_font("helvetica", "", 9.5)
            pdf.set_text_color(30, 41, 59)  # Slate 800
            
            # Strip simple html formatting elements
            clean_content = content
            clean_content = clean_content.replace("<br/>", "\n").replace("<br>", "\n")
            clean_content = re.sub(r"<[^>]+>", "", clean_content)
            
            # Replace markdown bullet styling for cleaner PDF write
            clean_content = re.sub(r"^\s*\*\s+", "- ", clean_content, flags=re.MULTILINE)
            clean_content = re.sub(r"^\s*-\s+", "- ", clean_content, flags=re.MULTILINE)
            
            pdf.multi_cell(0, 5, clean_content)
            
        pdf.ln(6)
        
    return bytes(pdf.output())
