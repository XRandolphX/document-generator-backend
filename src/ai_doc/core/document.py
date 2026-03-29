"""
document.py
-----------
Generación del documento Word y conversión a PDF.

Orquesta el flujo completo de producción del archivo final:
    1. Construye el prompt con ``prompt.modify_prompt()``.
    2. Llama al modelo DeepSeek vía OpenRouter en modo streaming.
    3. Parsea la respuesta con ``parser.process_response()``.
    4. Rellena la plantilla Word con ``DocxTemplate``.
    5. Convierte el ``.docx`` generado a PDF mediante LibreOffice.
"""

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


def calcular_tiempos(duracion_total: str) -> dict:
    match = re.search(r"\d+", duracion_total)
    total = int(match.group()) if match else 90

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
        clave: f"{round(total * proporcion)} min"
        for clave, proporcion in proporciones.items()
    }


def generate_document(session_params: dict, teacher_profile: dict) -> str:
    """
    Genera un documento Word a partir de los parámetros de la sesión
    y el perfil del docente.

    Flujo interno:
        1. Invoca ``modify_prompt()`` para construir el prompt.
        2. Realiza una solicitud en streaming al modelo
           ``deepseek/deepseek-chat-v3-0324:free`` vía OpenRouter.
        3. Concatena los chunks de la respuesta y los procesa con
           ``process_response()``.
        4. Combina los datos del docente, los parámetros de sesión y el
           contenido generado en un contexto para ``DocxTemplate``.
        5. Renderiza la plantilla ``class_template.docx`` y guarda el
           archivo resultante en ``generated_files/document_generated.docx``.

    Args:
        session_params (dict): Parámetros de la sesión de aprendizaje.
            Claves obligatorias: ``titulo``, ``grado_seccion``,
            ``numero_sesion``, ``nombre_modulo``, ``nombre_unidad``,
            ``duracion``, ``materiales_recursos``.
            Clave opcional: ``fecha`` (si se omite, se usa la fecha actual
            con formato ``"%d %b, %Y"``).
        teacher_profile (dict): Perfil del docente.
            Claves obligatorias: ``nombre_docente``, ``institucion_educativa``,
            ``area``, ``especialidad``, ``ciclo``, ``tipo_rubrica``.

    Returns:
        str: Ruta absoluta al archivo ``.docx`` generado.

    Raises:
        openai.APIError: Si la solicitud a la API de OpenRouter falla.
        FileNotFoundError: Si la plantilla ``class_template.docx`` no existe.
        Exception: Cualquier error inesperado durante el renderizado o guardado
            del documento.
    """
    prompt = modify_prompt(session_params, teacher_profile)

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)

    response_iterator = client.chat.completions.create(
        model="deepseek/deepseek-chat",
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
    tiempos = calcular_tiempos(session_params["duracion_total"])

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
        "duracion_total": session_params["duracion_total"],
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
        # Distribución de tiempos por proceso didáctico
        **tiempos,
    }

    output_dir = Path(__file__).parent.parent / "generated_files"
    output_dir.mkdir(exist_ok=True)
    doc_path = output_dir / "document_generated.docx"

    template_path = Path(__file__).parent.parent / "templates" / "sesion_template.docx"
    doc = DocxTemplate(template_path)
    doc.render(context)
    doc.save(doc_path)

    return str(doc_path)


def convert_to_pdf(doc_path: str) -> str:
    """
    Convierte un archivo ``.docx`` a PDF usando LibreOffice en modo headless.

    Ejecuta el comando ``soffice --headless --convert-to pdf`` en un
    subproceso. El archivo PDF se genera en el mismo directorio que el
    ``.docx`` de entrada y comparte su nombre base.

    Args:
        doc_path (str): Ruta absoluta al archivo ``.docx`` que se desea
            convertir. El archivo debe existir en el sistema de archivos.

    Returns:
        str: Ruta absoluta al archivo ``.pdf`` generado.

    Raises:
        FileNotFoundError: Si ``doc_path`` no corresponde a un archivo
            existente en el sistema de archivos.
        RuntimeError: Si LibreOffice termina con un código de error, o si el
            archivo PDF no aparece en el directorio de salida tras la
            conversión.

    Note:
        Requiere que ``soffice`` (LibreOffice) esté instalado y disponible
        en el PATH del sistema. En entornos de despliegue como Railway puede
        ser necesario configurar un buildpack adicional o usar una alternativa
        como Gotenberg.
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
