# Importando el modulo para interactuar con el sistema operativo
import os
# Importando la librería para trabajar con rutas de archivos
from pathlib import Path
# Importando la librería dotenv
from dotenv import load_dotenv
# Importando la libreria para Fechas y Horas 
from datetime import datetime
# Biblioteca para trabajar con documentos Word
from docxtpl import DocxTemplate
# Modulo de Expresiones Regulares
import re
# Cargar variables del .env
load_dotenv()
# Acceder a la API Key
api = os.getenv("API_KEY")
# Importar la librería de OpenAI
from openai import OpenAI

import subprocess
import sys
import time
import threading


# Funciones de procesamiento del prompt y respuesta
def modify_prompt(original_prompt):
    modified_prompt = (
        f"Basándote en el siguiente prompt del documento de sesión de aprendizaje: '{original_prompt}', "
        "por favor proporciona una respuesta estructurada sin ningún formato adicional (sin markdown, numerales, asteriscos ni encabezados). "
        "Cada sección debe estar en una línea con el siguiente formato: 'clave: contenido'. "
        "Las claves a generar son: title, competencia, desempeno, criterio, instrumentoevaluacion, evidencia, purpose, actitudes, antessession, recursos, inicio, situationproblem, preguntassituation, preguntainvestigation, hypothesis, preguntastema."
        "Asegúrate de que la respuesta siga exactamente este formato para evitar errores de coincidencia."
    )
    return modified_prompt

def remove_markdown(text):
    # Elimina los encabezados (líneas que comienzan con uno o más '#')
    text = re.sub(r'^\s*#{1,6}\s*', '', text, flags=re.MULTILINE)
        # Elimina caracteres de énfasis (asteriscos, guiones bajos, backticks)
    text = re.sub(r'[*_`]', '', text)
    # Opcionalmente, elimina otros caracteres típicos de Markdown (por ejemplo, '>', '[', ']', etc.)
    text = re.sub(r'[>\[\]]', '', text)
    return text

def process_response(response):
    """
    Procesa la respuesta y divide en secciones el documento de la sesión de aprendizaje.
    """

    # Limpia los espacios extra
    cleaned_response = re.sub(r'\s+', ' ', response).strip()
    # Elimina formato Markdown
    cleaned_response = remove_markdown(cleaned_response)

    # Define patrones usando lookahead para delimitar el final de cada sección sin capturarlo.
    patterns = {
        'title': re.compile(r'title:\s*(.*?)(?=competencia:|$)', re.DOTALL | re.IGNORECASE),
        'competencia': re.compile(r'competencia:\s*(.*?)(?=desempeno:|$)', re.DOTALL | re.IGNORECASE),
        'desempeno': re.compile(r'desempeno:\s*(.*?)(?=criterio:|$)', re.DOTALL | re.IGNORECASE),
        'criterio': re.compile(r'criterio:\s*(.*?)(?=instrumentoevaluacion:|$)', re.DOTALL | re.IGNORECASE),
        'instrumentoevaluacion': re.compile(r'instrumentoevaluacion:\s*(.*?)(?=evidencia:|$)', re.DOTALL | re.IGNORECASE),
        'evidencia': re.compile(r'evidencia:\s*(.*?)(?=purpose:|$)', re.DOTALL | re.IGNORECASE),
        'purpose': re.compile(r'purpose:\s*(.*?)(?=actitudes:|$)', re.DOTALL | re.IGNORECASE),
        'actitudes': re.compile(r'actitudes:\s*(.*?)(?=antessession:|$)', re.DOTALL | re.IGNORECASE),
        'antessession': re.compile(r'antessession:\s*(.*?)(?=recursos:|$)', re.DOTALL | re.IGNORECASE),
        'recursos': re.compile(r'recursos:\s*(.*?)(?=inicio:|$)', re.DOTALL | re.IGNORECASE),
        'inicio': re.compile(r'inicio:\s*(.*?)(?=situationproblem:|$)', re.DOTALL | re.IGNORECASE),
        'situationproblem': re.compile(r'situationproblem:\s*(.*?)(?=preguntassituation:|$)', re.DOTALL | re.IGNORECASE),
        'preguntassituation': re.compile(r'preguntassituation:\s*(.*?)(?=preguntainvestigation:|$)', re.DOTALL | re.IGNORECASE),
        'preguntainvestigation': re.compile(r'preguntainvestigation:\s*(.*?)(?=hypothesis:|$)', re.DOTALL | re.IGNORECASE),
        'hypothesis': re.compile(r'hypothesis:\s*(.*?)(?=preguntastema:|$)', re.DOTALL | re.IGNORECASE),
        'preguntastema': re.compile(r'preguntastema:\s*(.*)$', re.DOTALL | re.IGNORECASE)
    }

    sections = {}
    
    for key, pattern in patterns.items():
        match = pattern.search(cleaned_response)
        if match:
            # Capturamos el contenido de la sección (grupo 1)
            sections[key] = match.group(1).strip()
        else:
            sections[key] = "Respuesta incompleta"
    # Devuelve una tupla con los contenidos en el mismo orden de las keys
    return tuple(sections[key] for key in patterns.keys())
    
def convert_to_pdf(doc_path):
    if not os.path.isfile(doc_path):
        raise FileNotFoundError(f"El archivo {doc_path} no existe.")
    
    # Determinar la carpeta de salida (donde se encuentra el .docx)
    output_folder = os.path.dirname(doc_path)
    # Asegurarse de que la carpeta de salida existe
    os.makedirs(output_folder, exist_ok=True)

    # Nombre del archivo PDF: mismo que el .docx pero con extensión .pdf
    pdf_name = os.path.splitext(os.path.basename(doc_path))[0] + ".pdf"
    pdf_path = os.path.join(output_folder, pdf_name)

    try:
        # Pasar --outdir para que soffice genere el PDF
        subprocess.run(
            [
                "soffice", 
                "--headless", 
                "--convert-to", "pdf",
                "--outdir", output_folder, 
                doc_path
            ],
            check = True,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )
        # Comprobando en generated_files
        if not os.path.isfile(pdf_path):
            raise RuntimeError(
                f"Error en la conversión: el archivo PDF no fue generado en {output_folder}."
            )
        return pdf_path

    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="ignore")
        raise RuntimeError(f"Error ejecutando LibreOffice: {stderr}")

def generate_document(user_input): 
    # Inicializa el historial del chat y modifica el prompt
    chat_history = []
    prompt = modify_prompt(user_input)
    chat_history.append({"role": "user", "content": prompt})

    # Configurando el cliente con la API key y el base_url de DeepSeek
    client = OpenAI(
        base_url= "https://openrouter.ai/api/v1",
        api_key = api
        )
        
    response_iterator = client.chat.completions.create(
        model = "deepseek/deepseek-chat-v3-0324:free",
        messages = chat_history,
        stream = True,
    )

    # Procesando la respuesta
    collected_messages = []
    for chunk in response_iterator:
        delta_obj = chunk.choices[0].delta
        content = getattr(delta_obj, 'content', '')
        collected_messages.append(content)  
        full_reply_content = ''.join(collected_messages)
    print("\033[H\033[J", end="") # clear the terminal
    print(f"DeepSeek: {full_reply_content}")


    # Procesa la respuesta en secciones
    (title_GPT,competencias_capacidades_GPT, desempeno_GPT, criterio_GPT, instrumento_evaluacion_GPT,
     evidencia_GPT, purpose_GPT, actitudes_GPT, antes_session_GPT, recursos_GPT, inicio_GPT,
     situation_problem_GPT, preguntas_situation_GPT, pregunta_investigation_GPT, hypothesis_GPT,
     preguntas_tema_GPT) = process_response(full_reply_content)
    

    # Prepara el contexto para el documento
    fecha = datetime.today().strftime("%d %b, %Y")
    context = {
        'title': title_GPT,
        'competencias_capacidades': competencias_capacidades_GPT,
        'desempeno': desempeno_GPT,
        'criterio_evaluacion': criterio_GPT,
        'instrumento_evaluacion': instrumento_evaluacion_GPT,
        'evidencia': evidencia_GPT,
        'purpose': purpose_GPT,
        'actitudes': actitudes_GPT,
        'antes_session': antes_session_GPT,
        'recursos': recursos_GPT,
        'inicio': inicio_GPT,
        'situation_problem': situation_problem_GPT,
        'preguntas_situation': preguntas_situation_GPT,
        'pregunta_investigation': pregunta_investigation_GPT,
        'hypothesis': hypothesis_GPT,
        'preguntas_tema': preguntas_tema_GPT,
        'fecha': fecha
    }

    output_dir = os.path.join(os.path.dirname(__file__), "generated_files")
    os.makedirs(output_dir, exist_ok=True)
    doc_path = os.path.join(output_dir, "document_generated.docx")

    # Renderizar y guardar el documento
    template_path = os.path.join(os.path.dirname(__file__), "templates", "class_template.docx")
    doc = DocxTemplate(template_path)
    doc.render(context)
    doc.save(doc_path)

    # Convirtiendo el documento a PDF con LibreOffice
    pdf_path = convert_to_pdf(doc_path)
    
    return doc_path, pdf_path

    
# Lamada a la función

# Variable global para detener el spinner
stop_spinner = False

def spinner():
    """Muestra un spinner en consola hasta que stop_spinner sea True."""
    while not stop_spinner:
        for cursor in '|/-\\':
            sys.stdout.write(cursor)
            sys.stdout.flush()
            time.sleep(0.1)
            sys.stdout.write('\b')

if __name__ == "__main__":
    # Solicitar el tema al Usuario
    user_topic = input("Por favor, ingresa el tema de tu clase: ")

    # Iniciar el spinner en un hilo separado
    spinner_thread = threading.Thread(target=spinner)
    spinner_thread.start()

    try:
        doc_path, pdf_path = generate_document(user_topic)
        # Detener el spinner
        stop_spinner = True
        spinner_thread.join()
        print("\nDocumento generado: {}".format(doc_path))
        print("PDF generado: {}".format(pdf_path))
    except Exception as e:
        stop_spinner = True
        spinner_thread.join()
        print(f"\nError: {e}")