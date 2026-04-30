"""
parser.py
---------
Processes and cleans the plain text response returned by the AI model.
Extracts each section of the learning session using regular expressions
and organizes them into a structured dictionary.
"""

import json
import re


def remove_markdown(text: str) -> str:
    """
    Removes Markdown formatting from text.

    Strips the following elements:

    - Headers (``#`` at the start of a line).
    - Emphasis and inline code (``*``, `` ` ``).
    - Quote and link special characters (``>``, ``[``, ``]``).

    Note:
        Underscores (``_``) are intentionally preserved to keep
        underscore-based key names intact (e.g. ``indicador_logro``).

    Args:
        text (str): Text with possible Markdown formatting.

    Returns:
        str: Clean text without Markdown markers.
    """
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*`]", "", text)
    text = re.sub(r"[>\[\]]", "", text)
    return text


def process_response(response: str) -> dict:
    """
    Processes the AI response and splits it into sections
    corresponding to the learning session structure.

    Normalizes whitespace, strips Markdown formatting, and applies
    regular expressions to extract the content of each expected key.

    Patterns accept keys with or without underscores (e.g.
    ``indicador_logro`` or ``indicadorlogro``) to tolerate minor
    variations in the model's response.

    If a section is not found in the response, the fallback value
    ``"Respuesta incompleta"`` is assigned.

    The ``rubrica`` key receives special treatment: its content is
    parsed as JSON and returned as a list of dictionaries. If parsing
    fails, an empty list is returned.

    Args:
        response (str): Full text returned by the AI model,
            formatted as ``key: content`` per section.

    Returns:
        dict: Dictionary with one entry per session section.
            Dictionary keys:

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
            - ``rubrica`` (list[dict]): List of rubric criteria.
              Each dict contains the keys ``criterio``,
              ``logro_destacado``, ``logro_esperado``, ``en_proceso``
              and ``en_inicio``.

    Example:
        >>> sections = process_response(ai_raw_text)
        >>> print(sections["proposito"])
        'Que los estudiantes consoliden...'
        >>> print(sections["rubrica"])
        [{"criterio": "...", "logro_esperado": "...", ...}]
    """
    # Normalize whitespace and strip Markdown before extracting sections
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
            # Fallback value when a section is missing from the response
            sections[key] = "Respuesta incompleta"

    # Parse rubrica as JSON -> list of dicts
    rubrica_raw = sections.get("rubrica", "")
    try:
        # Wrap in [] if the AI omitted the outer brackets
        if rubrica_raw.strip() and not rubrica_raw.strip().startswith("["):
            rubrica_raw = f"[{rubrica_raw}]"
        sections["rubrica"] = json.loads(rubrica_raw)
    except (json.JSONDecodeError, TypeError):
        # Return empty list if JSON parsing fails
        sections["rubrica"] = []

    return sections
