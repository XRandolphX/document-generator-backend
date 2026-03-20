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
    try:
        data = request.get_json()

        if not data:
            return jsonify(
                success=False, error="No se recibieron datos en la solicitud."
            ), 400

        user_input = data.get("user_input")

        if not user_input or not user_input.strip():
            return jsonify(
                success=False,
                error="El campo user_input es requerido y no puede estar vacío.",
            ), 400

        doc_path = generate_document(user_input)
        pdf_path = convert_to_pdf(doc_path)

        return jsonify(success=True, pdf_path=pdf_path, docx_path=doc_path), 200

    except FileNotFoundError as e:
        return jsonify(success=False, error=f"Archivo no encontrado {str(e)}"), 404

    except RuntimeError as e:
        return jsonify(
            success=False, error=f"Error al generar el documento: {str(e)}"
        ), 500

    except Exception as e:
        return jsonify(success=False, error=f"Error inesperado{str(e)}"), 500


def create_app():
    return app
