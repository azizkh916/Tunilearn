from flask import Flask, request, render_template, send_file
import io
import fitz  # PyMuPDF
from fpdf import FPDF

app = Flask(__name__)

latest_summary_pdf = None

def extract_text_from_pdf(pdf_file):
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# Résumé basique sans NLTK / Sumy (évite erreur de tokenizer)
def summarize_text(text, sentence_count=5):
    sentences = text.replace('\n', ' ').split('. ')
    summary_sentences = sentences[:sentence_count]
    summary = '. '.join(summary_sentences)
    if not summary.endswith('.'):
        summary += '.'
    return summary

def create_pdf(summary_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    for line in summary_text.split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    output = io.BytesIO(pdf_bytes)
    output.seek(0)
    return output

@app.route('/', methods=['GET', 'POST'])
def index():
    summary = None
    global latest_summary_pdf
    if request.method == 'POST':
        pdf_file = request.files.get('pdf_file')
        if pdf_file and pdf_file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(pdf_file)
            summary = summarize_text(text, sentence_count=7)
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
