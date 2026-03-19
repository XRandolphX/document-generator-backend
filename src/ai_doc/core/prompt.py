def modify_prompt(original_prompt):
    modified_prompt = (
        f"Basándote en el siguiente prompt del documento de sesión de aprendizaje: '{original_prompt}', "
        "por favor proporciona una respuesta estructurada sin ningún formato adicional (sin markdown, numerales, asteriscos ni encabezados). "
        "Cada sección debe estar en una línea con el siguiente formato: 'clave: contenido'. "
        "Las claves a generar son: title, competencia, desempeno, criterio, instrumentoevaluacion, evidencia, purpose, actitudes, antessession, recursos, inicio, situationproblem, preguntassituation, preguntainvestigation, hypothesis, preguntastema."
        "Asegúrate de que la respuesta siga exactamente este formato para evitar errores de coincidencia."
    )
    return modified_prompt
