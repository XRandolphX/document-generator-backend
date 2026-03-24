"""
prompt.py
---------
Construcción del prompt estructurado que se envía al modelo de IA
para generar el contenido de la sesión de aprendizaje.
"""


def modify_prompt(session_params: dict, teacher_profile: dict) -> str:
    """
    Construye el prompt para la IA a partir de los parámetros
    de la sesión y el perfil del docente.

    El prompt instruye al modelo a responder en un formato de claves
    predefinidas (e.g. ``proposito:``, ``rubrica:``), sin markdown ni
    encabezados adicionales, para que ``parser.process_response()``
    pueda extraer cada sección de forma determinista.

    Args:
        session_params (dict): Parámetros de la sesión de aprendizaje.
            Claves esperadas:
                - titulo (str): Título de la sesión.
                - grado_seccion (str): Grado y sección del aula.
                - numero_sesion (str): Número correlativo de la sesión.
                - nombre_modulo (str): Nombre del módulo curricular.
                - nombre_unidad (str): Nombre de la unidad didáctica.
                - duracion (str): Duración total de la sesión (e.g. "90 min").
                - materiales_recursos (str): Materiales y recursos utilizados.
        teacher_profile (dict): Perfil del docente a cargo.
            Claves esperadas:
                - nombre_docente (str): Nombre completo del docente.
                - institucion_educativa (str): Nombre de la institución.
                - area (str): Área curricular.
                - especialidad (str): Especialidad del docente.
                - ciclo (str): Ciclo educativo (e.g. "VII").
                - tipo_rubrica (str): Tipo de rúbrica ("Analítica" u "Holística").

    Returns:
        str: Prompt completo listo para enviarse al modelo de IA.
    """
    return (
        f"Eres un experto en planificación curricular del sistema educativo peruano. "
        f"Genera una sesión de aprendizaje completa con los siguientes datos:\n\n"
        f"DATOS DEL DOCENTE:\n"
        f"- Institución Educativa: {teacher_profile['institucion_educativa']}\n"
        f"- Docente: {teacher_profile['nombre_docente']}\n"
        f"- Área: {teacher_profile['area']}\n"
        f"- Especialidad: {teacher_profile['especialidad']}\n"
        f"- Ciclo: {teacher_profile['ciclo']}\n"
        f"- Tipo de Rúbrica: {teacher_profile['tipo_rubrica']}\n\n"
        f"DATOS DE LA SESIÓN:\n"
        f"- Título: {session_params['titulo']}\n"
        f"- Grado y Sección: {session_params['grado_seccion']}\n"
        f"- Número de Sesión: {session_params['numero_sesion']}\n"
        f"- Nombre del Módulo: {session_params['nombre_modulo']}\n"
        f"- Nombre de la Unidad: {session_params['nombre_unidad']}\n"
        f"- Duración Total: {session_params['duracion']}\n"
        f"- Materiales y Recursos: {session_params['materiales_recursos']}\n\n"
        f"Responde ÚNICAMENTE en el siguiente formato exacto, sin markdown, "
        f"sin asteriscos, sin numerales, sin encabezados adicionales. "
        f"Cada clave en una línea con el formato 'clave: contenido':\n\n"
        f"proposito: ...\n"
        f"indicador_logro: ...\n"
        f"desempeno: ...\n"
        f"campo_tematico: ...\n"
        f"evidencia_proceso: ...\n"
        f"evidencia_producto_final: ...\n"
        f"evidencia_actuacion: ...\n"
        f"criterio_desempeno: ...\n"
        f"instrumento: ...\n"
        f"proposito_aprendizaje: ...\n"
        f"introduccion: ...\n"
        f"desarrollo_contenidos: ...\n"
        f"desarrollo_actividades: ...\n"
        f"evaluacion_formativa: ...\n"
        f"retroalimentacion: ...\n"
        f"cierre: ...\n"
        f"extension: ...\n"
        f"rubrica: ...\n"
    )
