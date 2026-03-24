import os
import subprocess
from datetime import datetime
from pathlib import Path

from docxtpl import DocxTemplate
from openai import OpenAI

from ai_doc.config import API_KEY
from ai_doc.core.parser import process_response
from ai_doc.core.prompt import modify_prompt


def generate_document(session_params: dict, teacher_profile: dict) -> str:
    """
    Genera un documento Word a partir de los parámetros de la sesión
    y el perfil del docente.
    """
    prompt = modify_prompt(session_params, teacher_profile)

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)

    response_iterator = client.chat.completions.create(
        model="deepseek/deepseek-chat-v3-0324:free",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    collected_messages = []
    for chunk in response_iterator:
        delta_obj = chunk.choices[0].delta
        content = getattr(delta_obj, "content", "")
        collected_messages.append(content)

    full_reply_content = "".join(collected_messages)

    sections = process_response(full_reply_content)

    context = {
        # Datos del docente
        "nombre_docente": teacher_profile["nombre_docente"],
        "institucion_educativa": teacher_profile["institucion_educativa"],
        "area": teacher_profile["area"],
        "especialidad": teacher_profile["especialidad"],
        "ciclo": teacher_profile["ciclo"],
        "tipo_rubrica": teacher_profile["tipo_rubrica"],
        # Datos de la sesión
        "titulo": session_params["titulo"],
        "grado_seccion": session_params["grado_seccion"],
        "numero_sesion": session_params["numero_sesion"],
        "nombre_modulo": session_params["nombre_modulo"],
        "nombre_unidad": session_params["nombre_unidad"],
        "fecha": session_params.get("fecha", datetime.today().strftime("%d %b, %Y")),
        "duracion": session_params["duracion"],
        "materiales_recursos": session_params["materiales_recursos"],
        # Contenido generado por la IA
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
        "rubrica": sections["rubrica"],
    }

    output_dir = Path(__file__).parent.parent / "generated_files"
    output_dir.mkdir(exist_ok=True)
    doc_path = output_dir / "document_generated.docx"

    template_path = Path(__file__).parent.parent / "templates" / "class_template.docx"
    doc = DocxTemplate(template_path)
    doc.render(context)
    doc.save(doc_path)

    return str(doc_path)


def convert_to_pdf(doc_path: str) -> str:
    """
    Convierte un archivo .docx a PDF usando LibreOffice.
    """
    if not os.path.isfile(doc_path):
        raise FileNotFoundError(f"El archivo {doc_path} no existe.")

    output_folder = os.path.dirname(doc_path)
    pdf_name = os.path.splitext(os.path.basename(doc_path))[0] + ".pdf"
    pdf_path = os.path.join(output_folder, pdf_name)

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
        if not os.path.isfile(pdf_path):
            raise RuntimeError(
                f"Error en la conversión: el archivo PDF no fue generado en {output_folder}."
            )
        return pdf_path

    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="ignore")
        raise RuntimeError(f"Error ejecutando LibreOffice: {stderr}")
