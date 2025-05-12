from app.utils.pdf_converter import text_to_pdf
import os

def main():
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Convert text to PDF
    text_file = 'data/test_policy.txt'
    pdf_file = 'data/test_policy.pdf'
    
    if os.path.exists(text_file):
        text_to_pdf(text_file, pdf_file)
        print(f"✅ Converted {text_file} to {pdf_file}")
    else:
        print(f"❌ Error: {text_file} not found")

if __name__ == "__main__":
    main() 