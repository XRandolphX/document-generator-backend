from flask import Flask, jsonify, request
from flask_cors import CORS

from ai_doc.core.document import convert_to_pdf, generate_document

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return "API de Flask está funcionando!"


@app.route("/generate-document", methods=["POST"])
def generate_document_endpoint():
    """
    Endpoint para generar un documento Word y PDF a partir del input del usuario.
    """
    data = request.get_json()
    user_input = data.get("user_input")

    doc_path = generate_document(user_input)
    pdf_path = convert_to_pdf(doc_path)

    return jsonify(success=True, pdf_path=pdf_path, docx_path=doc_path)


def create_app():
    return app
