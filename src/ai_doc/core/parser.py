import re


def remove_markdown(text):
    # Elimina encabezados (líneas que comienzan con uno o más '#')
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    # Elimina caracteres de énfasis (asteriscos, guiones bajos, backticks)
    text = re.sub(r"[*_`]", "", text)
    # Elimina otros caracteres típicos de Markdown
    text = re.sub(r"[>\[\]]", "", text)
    return text


def process_response(response):
    """
    Procesa la respuesta y divide en secciones el documento de la sesión de aprendizaje.
    """
    # Limpia los espacios extra
    cleaned_response = re.sub(r"\s+", " ", response).strip()
    # Elimina formato Markdown
    cleaned_response = remove_markdown(cleaned_response)

    patterns = {
        "title": re.compile(
            r"title:\s*(.*?)(?=competencia:|$)", re.DOTALL | re.IGNORECASE
        ),
        "competencia": re.compile(
            r"competencia:\s*(.*?)(?=desempeno:|$)", re.DOTALL | re.IGNORECASE
        ),
        "desempeno": re.compile(
            r"desempeno:\s*(.*?)(?=criterio:|$)", re.DOTALL | re.IGNORECASE
        ),
        "criterio": re.compile(
            r"criterio:\s*(.*?)(?=instrumentoevaluacion:|$)", re.DOTALL | re.IGNORECASE
        ),
        "instrumentoevaluacion": re.compile(
            r"instrumentoevaluacion:\s*(.*?)(?=evidencia:|$)", re.DOTALL | re.IGNORECASE
        ),
        "evidencia": re.compile(
            r"evidencia:\s*(.*?)(?=purpose:|$)", re.DOTALL | re.IGNORECASE
        ),
        "purpose": re.compile(
            r"purpose:\s*(.*?)(?=actitudes:|$)", re.DOTALL | re.IGNORECASE
        ),
        "actitudes": re.compile(
            r"actitudes:\s*(.*?)(?=antessession:|$)", re.DOTALL | re.IGNORECASE
        ),
        "antessession": re.compile(
            r"antessession:\s*(.*?)(?=recursos:|$)", re.DOTALL | re.IGNORECASE
        ),
        "recursos": re.compile(
            r"recursos:\s*(.*?)(?=inicio:|$)", re.DOTALL | re.IGNORECASE
        ),
        "inicio": re.compile(
            r"inicio:\s*(.*?)(?=situationproblem:|$)", re.DOTALL | re.IGNORECASE
        ),
        "situationproblem": re.compile(
            r"situationproblem:\s*(.*?)(?=preguntassituation:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "preguntassituation": re.compile(
            r"preguntassituation:\s*(.*?)(?=preguntainvestigation:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "preguntainvestigation": re.compile(
            r"preguntainvestigation:\s*(.*?)(?=hypothesis:|$)",
            re.DOTALL | re.IGNORECASE,
        ),
        "hypothesis": re.compile(
            r"hypothesis:\s*(.*?)(?=preguntastema:|$)", re.DOTALL | re.IGNORECASE
        ),
        "preguntastema": re.compile(
            r"preguntastema:\s*(.*)$", re.DOTALL | re.IGNORECASE
        ),
    }

    sections = {}

    for key, pattern in patterns.items():
        match = pattern.search(cleaned_response)
        if match:
            sections[key] = match.group(1).strip()
        else:
            sections[key] = "Respuesta incompleta"

    return tuple(sections[key] for key in patterns.keys())
