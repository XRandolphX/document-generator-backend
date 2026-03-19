import os
import subprocess
from datetime import datetime
from pathlib import Path

from docxtpl import DocxTemplate
from openai import OpenAI

from ai_doc.config import API_KEY
from ai_doc.core.parser import process_response
from ai_doc.core.prompt import modify_prompt


def generate_document(user_input):
    """
    Genera un documento Word y PDF a partir del input del usuario.
    """
    chat_history = []
    prompt = modify_prompt(user_input)
    chat_history.append({"role": "user", "content": prompt})

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)

    response_iterator = client.chat.completions.create(
        model="deepseek/deepseek-chat-v3-0324:free",
        messages=chat_history,
        stream=True,
    )

    collected_messages = []
    for chunk in response_iterator:
        delta_obj = chunk.choices[0].delta
        content = getattr(delta_obj, "content", "")
        collected_messages.append(content)

    full_reply_content = "".join(collected_messages)

    (
        title_GPT,
        competencias_capacidades_GPT,
        desempeno_GPT,
        criterio_GPT,
        instrumento_evaluacion_GPT,
        evidencia_GPT,
        purpose_GPT,
        actitudes_GPT,
        antes_session_GPT,
        recursos_GPT,
        inicio_GPT,
        situation_problem_GPT,
        preguntas_situation_GPT,
        pregunta_investigation_GPT,
        hypothesis_GPT,
        preguntas_tema_GPT,
    ) = process_response(full_reply_content)

    fecha = datetime.today().strftime("%d %b, %Y")

    context = {
        "title": title_GPT,
        "competencias_capacidades": competencias_capacidades_GPT,
        "desempeno": desempeno_GPT,
        "criterio_evaluacion": criterio_GPT,
        "instrumento_evaluacion": instrumento_evaluacion_GPT,
        "evidencia": evidencia_GPT,
        "purpose": purpose_GPT,
        "actitudes": actitudes_GPT,
        "antes_session": antes_session_GPT,
        "recursos": recursos_GPT,
        "inicio": inicio_GPT,
        "situation_problem": situation_problem_GPT,
        "preguntas_situation": preguntas_situation_GPT,
        "pregunta_investigation": pregunta_investigation_GPT,
        "hypothesis": hypothesis_GPT,
        "preguntas_tema": preguntas_tema_GPT,
        "fecha": fecha,
    }

    output_dir = Path(__file__).parent.parent / "generated_files"
    output_dir.mkdir(exist_ok=True)
    doc_path = output_dir / "document_generated.docx"

    template_path = Path(__file__).parent.parent / "templates" / "class_template.docx"
    doc = DocxTemplate(template_path)
    doc.render(context)
    doc.save(doc_path)

    return str(doc_path)


def convert_to_pdf(doc_path):
    """
    Convierte un archivo .docx a PDF usando LibreOffice.
    """
    if not os.path.isfile(doc_path):
        raise FileNotFoundError(f"El archivo {doc_path} no existe.")

    output_folder = os.path.dirname(doc_path)
    os.makedirs(output_folder, exist_ok=True)

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
