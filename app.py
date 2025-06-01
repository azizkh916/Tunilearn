
from flask import Flask, request, render_template, send_file
import os
import io
import fitz  # PyMuPDF
import nltk
from fpdf import FPDF
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
latest_summary_pdf = None

app = Flask(__name__)

nltk.download("punkt")
nltk.download("stopwords")

LANGUAGE = "french"

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
    pdf.set_font('DejaVu', '', 12)
    for line in summary_text.split("\n"):
        pdf.multi_cell(0, 10, line)

    # récupère le PDF en mémoire au format bytes (string)
    pdf_bytes = pdf.output(dest='S').encode('latin1')

    # place dans un BytesIO pour Flask
    output = io.BytesIO(pdf_bytes)
    output.seek(0)
    return output



@app.route('/', methods=['GET', 'POST'])
def index():
    summary = None
    if request.method == 'POST':
        pdf_file = request.files['pdf_file']
        if pdf_file.filename.endswith('.pdf'):
            full_text = extract_text_from_pdf(pdf_file)
            summary = summarize_text(full_text, sentence_count=7)
            global latest_summary_pdf
            latest_summary_pdf = create_pdf(summary)
    return render_template("index.html", summary=summary)

@app.route('/download')
def download_pdf():
    if latest_summary_pdf:
        return send_file(latest_summary_pdf, as_attachment=True, download_name="resume.pdf", mimetype='application/pdf')
    return "Aucun résumé disponible."

if __name__ == '__main__':
    app.run(debug=True)
