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
    Endpoint para generar un documento Word y PDF.
    Recibe los parámetros del docente y de la sesión.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify(
                success=False, error="No se recibieron datos en la solicitud."
            ), 400

        # Validar perfil del docente
        teacher_profile = data.get("teacher_profile")
        if not teacher_profile:
            return jsonify(
                success=False, error="El campo 'teacher_profile' es obligatorio."
            ), 400

        required_teacher_fields = [
            "nombre_docente",
            "institucion_educativa",
            "area",
            "especialidad",
            "ciclo",
            "tipo_rubrica",
        ]
        for field in required_teacher_fields:
            if not teacher_profile.get(field):
                return jsonify(
                    success=False,
                    error=f"El campo '{field}' del perfil del docente es obligatorio.",
                ), 400

        # Validar parámetros de la sesión
        session_params = data.get("session_params")
        if not session_params:
            return jsonify(
                success=False, error="El campo 'session_params' es obligatorio."
            ), 400

        required_session_fields = [
            "titulo",
            "grado_seccion",
            "numero_sesion",
            "nombre_modulo",
            "nombre_unidad",
            "duracion",
            "materiales_recursos",
        ]
        for field in required_session_fields:
            if not session_params.get(field):
                return jsonify(
                    success=False,
                    error=f"El campo '{field}' de la sesión es obligatorio.",
                ), 400

        doc_path = generate_document(session_params, teacher_profile)
        pdf_path = convert_to_pdf(doc_path)

        return jsonify(success=True, pdf_path=pdf_path, docx_path=doc_path), 200

    except FileNotFoundError as e:
        return jsonify(success=False, error=f"Archivo no encontrado: {str(e)}"), 404

    except RuntimeError as e:
        return jsonify(
            success=False, error=f"Error en la generación del documento: {str(e)}"
        ), 500

    except Exception as e:
        return jsonify(success=False, error=f"Error inesperado: {str(e)}"), 500


def create_app():
    return app
