"""
routes.py
---------
Flask API endpoint definitions.

Exposes two routes:
    - ``GET /``                   : API health check.
    - ``POST /generate-document`` : Generates a learning session in Word and PDF format.
"""

import logging

from flask import Flask, jsonify, request
from flask_cors import CORS

from ai_doc.core.document import convert_to_pdf, generate_document

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    """
    API health check.

    Returns:
        str: Confirmation message indicating the API is active.
    """
    return "Flask API is running!"


@app.route("/generate-document", methods=["POST"])
def generate_document_endpoint():
    """
    Generates a Word document and its PDF version from the teacher
    profile and learning session parameters.

    Validates the presence and completeness of all required fields in
    the request body before delegating generation to
    ``document.generate_document()`` and ``document.convert_to_pdf()``.

    Request Body (JSON):
        teacher_profile (dict): Teacher profile. Required fields:
            ``nombre_docente``, ``institucion_educativa``, ``area``,
            ``especialidad``, ``ciclo``, ``tipo_rubrica``.
        session_params (dict): Session parameters. Required fields:
            ``titulo``, ``grado_seccion``, ``numero_sesion``,
            ``nombre_modulo``, ``nombre_unidad``, ``duracion_total``,
            ``materiales_recursos``. Optional field: ``fecha``.

    Returns:
        Response: JSON with the following possible fields:

        - **200 OK** – Successful generation::

            {
                "success": true,
                "docx_path": "/path/to/document_generated.docx",
                "pdf_path": "/path/to/document_generated.pdf"
            }

        - **400 Bad Request** – Missing or invalid data::

            {"success": false, "error": "Description of the missing field."}

        - **404 Not Found** – Template or file not found::

            {"success": false, "error": "File not found: ..."}

        - **500 Internal Server Error** – Generation error or unexpected
          failure::

            {"success": false, "error": "Error description."}
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify(success=False, error="No data received in the request."), 400

        # Validate teacher profile
        teacher_profile = data.get("teacher_profile")
        if not teacher_profile:
            return jsonify(
                success=False, error="The 'teacher_profile' field is required."
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
                    error=f"The '{field}' field in teacher_profile is required.",
                ), 400

        # Validate session parameters
        session_params = data.get("session_params")
        if not session_params:
            return jsonify(
                success=False, error="The 'session_params' field is required."
            ), 400

        required_session_fields = [
            "titulo",
            "grado_seccion",
            "numero_sesion",
            "nombre_modulo",
            "nombre_unidad",
            "duracion_total",
            "materiales_recursos",
        ]
        for field in required_session_fields:
            if not session_params.get(field):
                return jsonify(
                    success=False,
                    error=f"The '{field}' field in session_params is required.",
                ), 400

        # Generate Word document and convert to PDF
        doc_path = generate_document(session_params, teacher_profile)
        pdf_path = convert_to_pdf(doc_path)

        return jsonify(success=True, pdf_path=pdf_path, docx_path=doc_path), 200

    except FileNotFoundError as e:
        return jsonify(success=False, error=f"File not found: {str(e)}"), 404

    except RuntimeError as e:
        return jsonify(success=False, error=f"Document generation error: {str(e)}"), 500

    except Exception as e:
        return jsonify(success=False, error=f"Unexpected error: {str(e)}"), 500


def create_app():
    """
    Flask application factory.

    Allows the ``app`` instance to be created from an external entry
    point (e.g. for testing or deployment with Gunicorn).

    Returns:
        Flask: Configured Flask application instance.
    """
    return app
