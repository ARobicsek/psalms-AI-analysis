#!/usr/bin/env python3
"""Extract text content from a Word document."""

from docx import Document
import sys

def extract_docx_content(file_path):
    """Extract all text from a DOCX file."""
    try:
        doc = Document(file_path)

        # Extract all paragraphs
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)

        return '\n\n'.join(full_text)
    except Exception as e:
        return f"Error reading document: {str(e)}"

if __name__ == "__main__":
    docx_path = "/home/user/psalms-AI-analysis/Documents/How Psalms Readers Guide works.docx"
    content = extract_docx_content(docx_path)
    print(content)
