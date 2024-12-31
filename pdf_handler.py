import fitz  # PyMuPDF for better text extraction


def extract_text_from_pdf(pdf_path):
    """
    Extracts and returns text from a PDF file.
    """
    text = ""
    try:
        with fitz.open(pdf_path) as pdf:
            for page_num in range(len(pdf)):
                page = pdf.load_page(page_num)
                text += page.get_text("text")  # Extract text in text mode
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text
