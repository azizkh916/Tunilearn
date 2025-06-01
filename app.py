import nltk
nltk.download("punkt")
nltk.download("stopwords")

from flask import Flask, request, render_template, send_file
import os
import io
import fitz  # PyMuPDF
from fpdf import FPDF
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

app = Flask(__name__)

LANGUAGE = "french"
latest_summary_pdf = None
import re

def clean_text(text):
    # Supprimer les caractères non supportés par Latin-1 (comme les emojis)
    return re.sub(r'[^\x00-\xff]', '', text)

def extract_text_from_pdf(pdf_file):
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def summarize_text(text, sentence_count=5):
    parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))
    stemmer = Stemmer(LANGUAGE)
    summarizer = LsaSummarizer(stemmer)
    summarizer.stop_words = get_stop_words(LANGUAGE)
    summary = summarizer(parser.document, sentence_count)
    return "\n".join(str(sentence) for sentence in summary)
def create_pdf(summary_text):
    pdf = FPDF()
    pdf.add_page()

    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', '', 14)
    pdf.multi_cell(0, 10, clean_text(summary_text))  # nettoyer ici

    return BytesIO(pdf.output(dest='S').encode('latin1'))


@app.route('/', methods=['GET', 'POST'])
def index():
    summary = None
    if request.method == 'POST':
        pdf_file = request.files['pdf_file']
        if pdf_file and pdf_file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(pdf_file)
            summary = summarize_text(text, sentence_count=7)
            global latest_summary_pdf
            latest_summary_pdf = create_pdf(summary)
    return render_template("index.html", summary=summary)

@app.route('/download-summary')
def download_summary():
    global latest_summary_pdf
    if latest_summary_pdf:
        return send_file(latest_summary_pdf, download_name="resume.pdf", as_attachment=True)
    return "Aucun résumé disponible", 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)

