from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def text_to_pdf(text_file_path: str, output_pdf_path: str):
    """Convert a text file to PDF"""
    # Read the text file
    with open(text_file_path, 'r') as file:
        text_content = file.read()
    
    # Create a PDF
    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    width, height = letter
    
    # Set font and size
    c.setFont("Helvetica", 12)
    
    # Split text into lines and write to PDF
    y = height - 50  # Start from top with margin
    for line in text_content.split('\n'):
        if y < 50:  # If we're near the bottom, start a new page
            c.showPage()
            c.setFont("Helvetica", 12)
            y = height - 50
        c.drawString(50, y, line)
        y -= 15  # Move down for next line
    
    c.save()
    return output_pdf_path 