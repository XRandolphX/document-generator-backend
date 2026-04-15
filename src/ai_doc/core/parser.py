"""
parser.py
---------
Procesamiento y limpieza de la respuesta en texto plano devuelta por el
modelo de IA. Extrae cada sección de la sesión de aprendizaje mediante
expresiones regulares y las organiza en un diccionario estructurado.
"""

import json
import re


def remove_markdown(text: str) -> str:
    """
    Elimina formato Markdown del texto.

    Remueve los siguientes elementos:

    - Encabezados (``#`` al inicio de línea).
    - Énfasis y código en línea (``*``, `` ` ``).
    - Caracteres especiales de cita y enlace (``>``, ``[``, ``]``).

    Note:
        Los guiones bajos (``_``) no se eliminan para preservar
        los nombres de clave con underscore (por ejemplo,
        ``indicador_logro``).

    Args:
        text (str): Texto con posible formato Markdown.

    Returns:
        str: Texto limpio sin marcadores Markdown.
    """
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*`]", "", text)
    text = re.sub(r"[>\[\]]", "", text)
    return text


def process_response(response: str) -> dict:
    """
    Procesa la respuesta de la IA y la divide en secciones
    correspondientes a la sesión de aprendizaje.

    Normaliza los espacios en blanco, elimina el formato Markdown y aplica
    expresiones regulares para extraer el contenido de cada clave esperada.

    Los patrones aceptan claves con o sin guión bajo (por ejemplo,
    ``indicador_logro`` o ``indicadorlogro``) para tolerar variaciones
    menores en la respuesta del modelo.

    Si una sección no se encuentra en la respuesta, se asigna el valor
    ``"Respuesta incompleta"`` como fallback.

    La clave ``rubrica`` recibe un tratamiento especial: su contenido se
    parsea como JSON y se devuelve como lista de diccionarios. Si el
    parseo falla, se devuelve una lista vacía.

    Args:
        response (str): Texto completo devuelto por el modelo de IA,
            con el formato ``clave: contenido`` por sección.

    Returns:
        dict: Diccionario con una entrada por cada sección de la sesión.
            Claves del diccionario:

            - ``proposito``
            - ``indicador_logro``
            - ``desempeno``
            - ``campo_tematico``
            - ``evidencia_proceso``
            - ``evidencia_producto_final``
            - ``evidencia_actuacion``
            - ``criterio_desempeno``
            - ``instrumento``
            - ``proposito_aprendizaje``
            - ``introduccion``
            - ``desarrollo_contenidos``
            - ``desarrollo_actividades``
            - ``evaluacion_formativa``
            - ``retroalimentacion``
            - ``cierre``
            - ``extension``
            - ``rubrica`` (list[dict]): Lista de criterios de la rúbrica.
              Cada dict contiene las claves ``criterio``,
              ``logro_destacado``, ``logro_esperado``, ``en_proceso``
              y ``en_inicio``.

    Example:
        >>> sections = process_response(ai_raw_text)
        >>> print(sections["proposito"])
        'Que los estudiantes consoliden...'
        >>> print(sections["rubrica"])
        [{"criterio": "...", "logro_esperado": "...", ...}]
    """
    cleaned_response = re.sub(r"\s+", " ", response).strip()
    cleaned_response = remove_markdown(cleaned_response)

    patterns = {
        "proposito": re.compile(
            r"proposito:\s*(.*?)(?=indicador_?logro:|$)", re.DOTALL | re.IGNORECASE
        ),
        "indicador_logro": re.compile(
            r"indicador_?logro:\s*(.*?)(?=desempe[nñ]o:|$)", re.DOTALL | re.IGNORECASE
        ),
        "desempeno": re.compile(
            r"desempe[nñ]o:\s*(.*?)(?=campo_?tematico:|$)", re.DOTALL | re.IGNORECASE
        ),
        "campo_tematico": re.compile(
            r"campo_?tematico:\s*(.*?)(?=evidencia_?proceso:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "evidencia_proceso": re.compile(
            r"evidencia_?proceso:\s*(.*?)(?=evidencia_?producto_?final:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "evidencia_producto_final": re.compile(
            r"evidencia_?producto_?final:\s*(.*?)(?=evidencia_?actuacion:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "evidencia_actuacion": re.compile(
            r"evidencia_?actuacion:\s*(.*?)(?=criterio_?desempe[nñ]o:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "criterio_desempeno": re.compile(
            r"criterio_?desempe[nñ]o:\s*(.*?)(?=instrumento:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "instrumento": re.compile(
            r"instrumento:\s*(.*?)(?=proposito_?aprendizaje:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "proposito_aprendizaje": re.compile(
            r"proposito_?aprendizaje:\s*(.*?)(?=introduccion:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "introduccion": re.compile(
            r"introduccion:\s*(.*?)(?=desarrollo_?contenidos:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "desarrollo_contenidos": re.compile(
            r"desarrollo_?contenidos:\s*(.*?)(?=desarrollo_?actividades:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "desarrollo_actividades": re.compile(
            r"desarrollo_?actividades:\s*(.*?)(?=evaluacion_?formativa:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "evaluacion_formativa": re.compile(
            r"evaluacion_?formativa:\s*(.*?)(?=retroalimentacion:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "retroalimentacion": re.compile(
            r"retroalimentacion:\s*(.*?)(?=cierre:|$)", re.DOTALL | re.IGNORECASE
        ),
        "cierre": re.compile(
            r"cierre:\s*(.*?)(?=extension:|$)", re.DOTALL | re.IGNORECASE
        ),
        "extension": re.compile(
            r"extension:\s*(.*?)(?=rubrica:|$)", re.DOTALL | re.IGNORECASE
        ),
        "rubrica": re.compile(r"rubrica:\s*(.*)$", re.DOTALL | re.IGNORECASE),
    }

    sections = {}
    for key, pattern in patterns.items():
        match = pattern.search(cleaned_response)
        if match:
            sections[key] = match.group(1).strip()
        else:
            sections[key] = "Respuesta incompleta"

    # Parsear rubrica como JSON -> lista de dicts
    rubrica_raw = sections.get("rubrica", "")
    try:
        # Envolver en [] si la IA omitió los corchetes externos
        if rubrica_raw.strip() and not rubrica_raw.strip().startswith("["):
            rubrica_raw = f"[{rubrica_raw}]"
        sections["rubrica"] = json.loads(rubrica_raw)
    except (json.JSONDecodeError, TypeError):
        sections["rubrica"] = []

    return sections
