"""Mock text extraction module"""

async def extract_text_from_file(file_path: str) -> str:
    """Extract text from file - mock implementation"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return "Mock extracted text content"