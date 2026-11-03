from PyPDF2 import PdfReader

from ai_modules.chatbot import chatbot_response


def summarize_pdf(pdf_path):

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:

        text += page.extract_text()

    prompt = f"""
Summarize this PDF content:

{text[:4000]}
"""

    summary = chatbot_response(prompt)

    return summary