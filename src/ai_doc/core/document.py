"""
document.py
-----------
Word document generation and PDF conversion.

Orchestrates the complete production flow of the final file:
    1. Builds the prompt with ``prompt.modify_prompt()``.
    2. Calls the DeepSeek model via OpenRouter in streaming mode.
    3. Parses the response with ``parser.process_response()``.
    4. Fills the Word template with ``DocxTemplate``.
    5. Converts the generated ``.docx`` to PDF using LibreOffice.
"""

import logging
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

from docxtpl import DocxTemplate
from openai import OpenAI

from ai_doc.config import API_KEY
from ai_doc.core.parser import process_response
from ai_doc.core.prompt import modify_prompt

logger = logging.getLogger(__name__)


def calcular_tiempos(duracion_total: str) -> dict:
    """
    Calculates the time distribution per didactic process
    based on the total session duration.

    Extracts the numeric value from ``duracion_total`` and distributes
    it proportionally across the eight session moments. If no valid
    number is found, defaults to 90 minutes.

    Args:
        duracion_total (str): Total session duration, for example
            ``"90 min"`` or ``"120 minutos"``.

    Returns:
        dict: Dictionary with eight keys, each holding the assigned
        time in ``"N min"`` format. Keys:

        - ``tiempo_proposito_aprendizaje``
        - ``tiempo_introduccion``
        - ``tiempo_desarrollo_contenidos``
        - ``tiempo_desarrollo_actividades``
        - ``tiempo_evaluacion_formativa``
        - ``tiempo_retroalimentacion``
        - ``tiempo_cierre``
        - ``tiempo_extension``
    """
    match = re.search(r"\d+", duracion_total)
    total = (
        int(match.group()) if match else 90
    )  # Default to 90 minutes if no number found

    proporciones = {
        "tiempo_proposito_aprendizaje": 0.056,
        "tiempo_introduccion": 0.111,
        "tiempo_desarrollo_contenidos": 0.167,
        "tiempo_desarrollo_actividades": 0.389,
        "tiempo_evaluacion_formativa": 0.111,
        "tiempo_retroalimentacion": 0.056,
        "tiempo_cierre": 0.056,
        "tiempo_extension": 0.056,
    }

    return {
        key: f"{round(total * proportion)} min"
        for key, proportion in proporciones.items()
    }


def generate_document(session_params: dict, teacher_profile: dict) -> str:
    """
    Generates a Word document from the session parameters
    and the teacher profile.

    Internal flow:
        1. Calls ``modify_prompt()`` to build the prompt.
        2. Sends a streaming request to the ``deepseek/deepseek-chat``
           model via OpenRouter.
        3. Concatenates the response chunks and processes them with
           ``process_response()``.
        4. Combines teacher data, session parameters, time distribution,
           and generated content into a context for ``DocxTemplate``.
        5. Renders the ``sesion_template.docx`` template and saves the
           result to ``generated_files/document_generated.docx``.

    Args:
        session_params (dict): Learning session parameters.
            Required keys: ``titulo``, ``grado_seccion``,
            ``numero_sesion``, ``nombre_modulo``, ``nombre_unidad``,
            ``duracion_total``, ``materiales_recursos``.
            Optional key: ``fecha`` (if omitted, today's date is used
            in ``"%d %b, %Y"`` format).
        teacher_profile (dict): Teacher profile.
            Required keys: ``nombre_docente``, ``institucion_educativa``,
            ``area``, ``especialidad``, ``ciclo``, ``tipo_rubrica``.

    Returns:
        str: Absolute path to the generated ``.docx`` file.

    Raises:
        openai.APIError: If the OpenRouter API request fails.
        FileNotFoundError: If the ``sesion_template.docx`` template
            does not exist in the ``templates/`` directory.
        Exception: Any unexpected error during rendering or saving
            the document.
    """
    prompt = modify_prompt(session_params, teacher_profile)
    logger.info("Prompt built for session: %s", session_params["titulo"])

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)

    response_iterator = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    logger.info("Streaming response from DeepSeek via OpenRouter...")

    # Accumulate all stream chunks before parsing
    collected_messages = []
    for chunk in response_iterator:
        delta_obj = chunk.choices[0].delta
        content = getattr(delta_obj, "content", "")
        collected_messages.append(content)

    full_reply_content = "".join(collected_messages)
    logger.info("Response received — %d characters", len(full_reply_content))

    sections = process_response(full_reply_content)
    logger.info("Sections parsed: %s", list(sections.keys()))

    tiempos = calcular_tiempos(session_params["duracion_total"])

    context = {
        # Teacher data
        "nombre_docente": teacher_profile["nombre_docente"],
        "institucion_educativa": teacher_profile["institucion_educativa"],
        "area": teacher_profile["area"],
        "especialidad": teacher_profile["especialidad"],
        "ciclo": teacher_profile["ciclo"],
        "tipo_rubrica": teacher_profile["tipo_rubrica"],
        # Session data
        "titulo": session_params["titulo"],
        "grado_seccion": session_params["grado_seccion"],
        "numero_sesion": session_params["numero_sesion"],
        "nombre_modulo": session_params["nombre_modulo"],
        "nombre_unidad": session_params["nombre_unidad"],
        "fecha": session_params.get("fecha", datetime.today().strftime("%d %b, %Y")),
        "duracion_total": session_params["duracion_total"],
        "materiales_recursos": session_params["materiales_recursos"],
        # AI-generated content
        "proposito": sections["proposito"],
        "indicador_logro": sections["indicador_logro"],
        "desempeno": sections["desempeno"],
        "campo_tematico": sections["campo_tematico"],
        "evidencia_proceso": sections["evidencia_proceso"],
        "evidencia_producto_final": sections["evidencia_producto_final"],
        "evidencia_actuacion": sections["evidencia_actuacion"],
        "criterio_desempeno": sections["criterio_desempeno"],
        "instrumento": sections["instrumento"],
        "proposito_aprendizaje": sections["proposito_aprendizaje"],
        "introduccion": sections["introduccion"],
        "desarrollo_contenidos": sections["desarrollo_contenidos"],
        "desarrollo_actividades": sections["desarrollo_actividades"],
        "evaluacion_formativa": sections["evaluacion_formativa"],
        "retroalimentacion": sections["retroalimentacion"],
        "cierre": sections["cierre"],
        "extension": sections["extension"],
        "filas_rubrica": sections["rubrica"],
        # Time distribution per didactic process
        **tiempos,
    }

    # Create output directory if it does not exist
    output_dir = Path(__file__).parent.parent / "generated_files"
    output_dir.mkdir(exist_ok=True)
    doc_path = output_dir / "document_generated.docx"

    # Load template, render context and save the generated document
    template_path = Path(__file__).parent.parent / "templates" / "sesion_template.docx"
    doc = DocxTemplate(template_path)
    doc.render(context)
    doc.save(doc_path)
    logger.info("Document saved: %s", doc_path)

    return str(doc_path)


def convert_to_pdf(doc_path: str) -> str:
    """
    Converts a ``.docx`` file to PDF using LibreOffice in headless mode.

    Runs the ``soffice --headless --convert-to pdf`` command in a
    subprocess. The PDF file is generated in the same directory as the
    input ``.docx`` and shares its base name.

    Args:
        doc_path (str): Absolute path to the ``.docx`` file to convert.
            The file must exist on the filesystem.

    Returns:
        str: Absolute path to the generated ``.pdf`` file.

    Raises:
        FileNotFoundError: If ``doc_path`` does not correspond to an
            existing file on the filesystem.
        RuntimeError: If LibreOffice exits with an error code, or if the
            PDF file does not appear in the output directory after
            conversion.

    Note:
        Requires ``soffice`` (LibreOffice) to be installed and available
        on the system PATH. In deployment environments such as Railway,
        a buildpack that includes LibreOffice may be required, or an
        alternative like Gotenberg (https://gotenberg.dev) should be
        considered.
    """
    if not os.path.isfile(doc_path):
        raise FileNotFoundError(f"File not found: {doc_path}")

    output_folder = os.path.dirname(doc_path)
    pdf_name = os.path.splitext(os.path.basename(doc_path))[0] + ".pdf"
    pdf_path = os.path.join(output_folder, pdf_name)

    logger.info("Converting to PDF: %s", doc_path)

    try:
        subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                output_folder,
                doc_path,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Verify the PDF was actually created after conversion
        if not os.path.isfile(pdf_path):
            raise RuntimeError(
                f"Conversion error: PDF file was not generated in {output_folder}."
            )
        logger.info("Conversion successful: %s", pdf_path)
        return pdf_path

    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="ignore")
        raise RuntimeError(f"LibreOffice execution error: {stderr}")
