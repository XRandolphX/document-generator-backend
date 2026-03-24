"""
parser.py
---------
Procesamiento y limpieza de la respuesta en texto plano devuelta por el
modelo de IA. Extrae cada sección de la sesión de aprendizaje mediante
expresiones regulares y las organiza en un diccionario estructurado.
"""

import re


def remove_markdown(text: str) -> str:
    """
    Elimina formato Markdown del texto.

    Remueve los siguientes elementos:
        - Encabezados (``#`` al inicio de línea).
        - Énfasis y código en línea (``*``, ``_``, `` ` ``).
        - Caracteres especiales de cita y enlace (``>``, ``[``, ``]``).

    Args:
        text (str): Texto con posible formato Markdown.

    Returns:
        str: Texto limpio sin marcadores Markdown.
    """
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_`]", "", text)
    text = re.sub(r"[>\[\]]", "", text)
    return text


def process_response(response: str) -> dict:
    """
    Procesa la respuesta de la IA y la divide en secciones
    correspondientes a la sesión de aprendizaje.

    Normaliza los espacios en blanco, elimina el formato Markdown y aplica
    expresiones regulares para extraer el contenido de cada clave esperada.
    Si una sección no se encuentra en la respuesta, se asigna el valor
    ``"Respuesta incompleta"`` como fallback.

    Las secciones extraídas siguen el orden del formato solicitado al modelo
    en ``prompt.modify_prompt()``.

    Args:
        response (str): Texto completo devuelto por el modelo de IA,
            con el formato ``clave: contenido`` por línea.

    Returns:
        dict: Diccionario con una entrada por cada sección de la sesión.
            Claves del diccionario:
                - proposito
                - indicador_logro
                - desempeno
                - campo_tematico
                - evidencia_proceso
                - evidencia_producto_final
                - evidencia_actuacion
                - criterio_desempeno
                - instrumento
                - proposito_aprendizaje
                - introduccion
                - desarrollo_contenidos
                - desarrollo_actividades
                - evaluacion_formativa
                - retroalimentacion
                - cierre
                - extension
                - rubrica

    Example:
        >>> sections = process_response(ai_raw_text)
        >>> print(sections["proposito"])
        'Que los estudiantes consoliden...'
    """
    cleaned_response = re.sub(r"\s+", " ", response).strip()
    cleaned_response = remove_markdown(cleaned_response)

    patterns = {
        "proposito": re.compile(
            r"proposito:\s*(.*?)(?=indicador_logro:|$)", re.DOTALL | re.IGNORECASE
        ),
        "indicador_logro": re.compile(
            r"indicador_logro:\s*(.*?)(?=desempeno:|$)", re.DOTALL | re.IGNORECASE
        ),
        "desempeno": re.compile(
            r"desempeno:\s*(.*?)(?=campo_tematico:|$)", re.DOTALL | re.IGNORECASE
        ),
        "campo_tematico": re.compile(
            r"campo_tematico:\s*(.*?)(?=evidencia_proceso:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "evidencia_proceso": re.compile(
            r"evidencia_proceso:\s*(.*?)(?=evidencia_producto_final:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "evidencia_producto_final": re.compile(
            r"evidencia_producto_final:\s*(.*?)(?=evidencia_actuacion:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "evidencia_actuacion": re.compile(
            r"evidencia_actuacion:\s*(.*?)(?=criterio_desempeno:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "criterio_desempeno": re.compile(
            r"criterio_desempeno:\s*(.*?)(?=instrumento:|$)", re.DOTALL | re.IGNORECASE
        ),
        "instrumento": re.compile(
            r"instrumento:\s*(.*?)(?=proposito_aprendizaje:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "proposito_aprendizaje": re.compile(
            r"proposito_aprendizaje:\s*(.*?)(?=introduccion:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "introduccion": re.compile(
            r"introduccion:\s*(.*?)(?=desarrollo_contenidos:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "desarrollo_contenidos": re.compile(
            r"desarrollo_contenidos:\s*(.*?)(?=desarrollo_actividades:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "desarrollo_actividades": re.compile(
            r"desarrollo_actividades:\s*(.*?)(?=evaluacion_formativa:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "evaluacion_formativa": re.compile(
            r"evaluacion_formativa:\s*(.*?)(?=retroalimentacion:|$)",
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

    return sections
