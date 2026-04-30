"""
prompt.py
---------
Builds the structured prompt sent to the AI model to generate
the learning session content.
"""


def modify_prompt(session_params: dict, teacher_profile: dict) -> str:
    """
    Builds the prompt for the AI model from the session parameters
    and the teacher profile.

    The prompt instructs the model to respond in a format of predefined
    keys (e.g. ``proposito:``, ``rubrica:``), without markdown or
    additional headers, so that ``parser.process_response()`` can extract
    each section deterministically.

    The rubric is requested in JSON format with the achievement levels
    ``logro_destacado``, ``logro_esperado``, ``en_proceso`` and
    ``en_inicio``, derived from the session performance and criteria.
    The rubric type (``"Analítica"`` or ``"Holística"``) determines
    its structure.

    Args:
        session_params (dict): Learning session parameters.
            Expected keys:

            - ``titulo`` (str): Session title.
            - ``grado_seccion`` (str): Grade and classroom section.
            - ``numero_sesion`` (str): Sequential session number.
            - ``nombre_modulo`` (str): Curricular module name.
            - ``nombre_unidad`` (str): Didactic unit name.
            - ``duracion_total`` (str): Total duration (e.g. ``"90 min"``).
            - ``materiales_recursos`` (str): Materials and resources.

        teacher_profile (dict): Profile of the teacher in charge.
            Expected keys:

            - ``nombre_docente`` (str): Teacher's full name.
            - ``institucion_educativa`` (str): Institution name.
            - ``area`` (str): Curricular area.
            - ``especialidad`` (str): Teacher's specialization.
            - ``ciclo`` (str): Educational cycle (e.g. ``"VII"``).
            - ``tipo_rubrica`` (str): Rubric type
              (``"Analítica"`` or ``"Holística"``).

    Returns:
        str: Complete prompt ready to be sent to the AI model.
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
        f"- Duración Total: {session_params['duracion_total']}\n"
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
        f"rubrica: Genera una rúbrica {teacher_profile['tipo_rubrica']} basada en los campos "
        f"temáticos de la sesión. "
        f"Usa como referencia el desempeño y los criterios de desempeño proporcionados. "
        f"El nivel 'Logro Esperado' debe derivarse del desempeño, y los demás niveles "
        f"(Logro Destacado, En Proceso, En Inicio) deben derivarse de este. "
        f"Responde ÚNICAMENTE con un JSON válido, sin texto adicional, sin markdown, "
        f"sin comillas extras. "
        f"El formato debe ser exactamente este:\n"
        f'[{{"criterio": "Nombre del criterio", "logro_destacado": "...", "logro_esperado": "...", '
        f'"en_proceso": "...", "en_inicio": "..."}}]\n'
    )
