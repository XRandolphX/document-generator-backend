# Document Generator Backend

Backend en Flask que genera sesiones de aprendizaje completas para docentes peruanos usando IA. El docente ingresa sus datos y el tema, y el sistema produce automáticamente un documento Word listo para usar, con su versión en PDF.

> **Estado:** Backend completo y funcional. Frontend React en desarrollo.

---

## Capturas

<!-- Request y response en Postman / Thunder Client -->
![Request en Postman](docs/demo-postman.png)

<!-- Documento Word generado por el sistema -->
![Documento Word generado](docs/demo-output-docx.png)

<!-- PDF generado por LibreOffice -->
![PDF generado](docs/demo-output-pdf.png)

---

## Tabla de contenidos

- [Capturas](#capturas)
- [Demo del flujo](#demo-del-flujo)
- [Tecnologías](#tecnologías)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Instalación local](#instalación-local)
- [Uso de la API](#uso-de-la-api)
- [Secciones generadas por la IA](#secciones-generadas-por-la-ia)
- [Deploy](#deploy)
- [Flujo de trabajo Git](#flujo-de-trabajo-git)
- [Autor](#autor)

---

## Demo del flujo

```
Docente llena el formulario (frontend React)
        ↓
POST /generate-document
        ↓
routes.py → valida teacher_profile y session_params
        ↓
core/prompt.py → construye el prompt con los datos del docente y la sesión
        ↓
DeepSeek API (vía OpenRouter) → genera el contenido en streaming
        ↓
core/parser.py → extrae cada sección de la respuesta mediante regex
        ↓
core/document.py → DocxTemplate rellena la plantilla Word + LibreOffice convierte a PDF
        ↓
Devuelve doc_path y pdf_path al frontend
```

---

## Tecnologías

| Tecnología | Uso |
|---|---|
| Python 3.x | Lenguaje principal |
| Flask | Framework web |
| Flask-CORS | Manejo de CORS para el frontend React |
| Poetry | Gestión de dependencias |
| DocxTemplate | Renderizado de la plantilla Word con variables |
| OpenAI SDK | Cliente HTTP para OpenRouter / DeepSeek |
| python-dotenv | Carga de variables de entorno desde `.env` |
| LibreOffice (`soffice`) | Conversión de `.docx` a PDF en modo headless |

---

## Estructura del proyecto

```
document-generator-backend/
├── src/
│   └── ai_doc/
│       ├── __init__.py
│       ├── config.py               # Carga de variables de entorno
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes.py           # Endpoints Flask
│       ├── core/
│       │   ├── __init__.py
│       │   ├── prompt.py           # Construcción del prompt para la IA
│       │   ├── parser.py           # Extracción de secciones de la respuesta
│       │   └── document.py         # Generación del .docx y conversión a PDF
│       ├── templates/
│       │   └── sesion_template.docx  # Plantilla Word con variables DocxTemplate
│       └── generated_files/
│           └── .gitkeep            # Carpeta gitignoreada para archivos generados
├── tests/
│   └── __init__.py
├── .env.example
├── .gitignore
├── .python-version
├── poetry.lock
├── pyproject.toml
└── README.md
```

---

## Instalación local

### Requisitos previos

- Python 3.x
- [Poetry](https://python-poetry.org/docs/#installation)
- [LibreOffice](https://www.libreoffice.org/download/download/) (para la conversión a PDF)
- Una API key de [OpenRouter](https://openrouter.ai)

En Ubuntu / Debian puedes instalar LibreOffice directamente desde la terminal:

```bash
sudo apt update
sudo apt install libreoffice-writer -y
```

### Pasos

**1. Clonar el repositorio**

```bash
git clone https://github.com/tu-usuario/document-generator-backend.git
cd document-generator-backend
```

**2. Instalar dependencias**

```bash
poetry install
```

> Si solo quieres instalar las dependencias sin el paquete del proyecto:
> ```bash
> poetry install --no-root
> ```

**2.1. (Opcional) Generar el entorno virtual dentro del proyecto**

Por defecto Poetry guarda los entornos en `~/.cache/pypoetry/virtualenvs/`. Si prefieres tenerlo dentro de la carpeta del proyecto (útil para VSCode y otros editores):

```bash
poetry config virtualenvs.in-project true
poetry env remove <nombre-del-env-en-cache>  # elimina el env cacheado si ya existe
poetry install
```

Para activar el entorno manualmente:

```bash
source .venv/bin/activate
# o
poetry env activate <nombre-del-env>
```

**3. Configurar variables de entorno**

Crea un archivo `.env` en la raíz del proyecto basándote en el ejemplo incluido:

```bash
cp .env.example .env
```

Edita `.env` y agrega tu API key:

```env
API_KEY=tu_api_key_de_openrouter
```

**4. Correr el servidor**

```bash
poetry run flask --app src/ai_doc/api/routes.py run
```

El servidor queda disponible en `http://localhost:5000`.

---

## Uso de la API

### `GET /`

Health check. Confirma que el servidor está activo.

**Response:**
```
API de Flask está funcionando!
```

---

### `POST /generate-document`

Genera una sesión de aprendizaje completa en formato Word y PDF.

**Request Body:**

```json
{
  "teacher_profile": {
    "nombre_docente": "Randolph Fabrizio Ramirez Palacios",
    "institucion_educativa": "Fe y Alegría 18 - Sullana",
    "area": "Educación para el Trabajo",
    "especialidad": "Computación e Informática",
    "ciclo": "VII",
    "tipo_rubrica": "Analítica"
  },
  "session_params": {
    "titulo": "Taller de Consolidación: Revisión y Avance del Proyecto",
    "grado_seccion": "4to. A, B, C, D",
    "numero_sesion": "40",
    "nombre_modulo": "Habilidades de gestión de proyectos de emprendimiento económico o social",
    "nombre_unidad": "Aplicar estrategias para captar y retener clientes",
    "fecha": "29/10/2025",
    "duracion_total": "90 min",
    "materiales_recursos": "Laptop (Chromebook), Pizarra"
  }
}
```

> El campo `fecha` es opcional. Si se omite, se usa la fecha del día en formato `DD Mon, YYYY`.

**Responses:**

| Código | Descripción |
|---|---|
| `200 OK` | Generación exitosa. Devuelve `docx_path` y `pdf_path`. |
| `400 Bad Request` | Campo obligatorio faltante o inválido. |
| `404 Not Found` | Plantilla o archivo no encontrado. |
| `500 Internal Server Error` | Error en la generación o en LibreOffice. |

**Response exitosa (200):**
```json
{
  "success": true,
  "docx_path": "/ruta/al/document_generated.docx",
  "pdf_path": "/ruta/al/document_generated.pdf"
}
```

**Response de error (400):**
```json
{
  "success": false,
  "error": "El campo 'titulo' de la sesión es obligatorio."
}
```

---

## Secciones generadas por la IA

La IA genera automáticamente el contenido de las siguientes secciones, que se inyectan en la plantilla Word:

| Clave | Descripción |
|---|---|
| `proposito` | Propósito general de la sesión |
| `indicador_logro` | Indicador de logro esperado |
| `desempeno` | Desempeño del estudiante |
| `campo_tematico` | Campo temático de la sesión |
| `evidencia_proceso` | Evidencia de productos del proceso |
| `evidencia_producto_final` | Evidencia del producto final |
| `evidencia_actuacion` | Evidencia de actuación |
| `criterio_desempeno` | Criterio de desempeño para evaluación |
| `instrumento` | Instrumento de evaluación |
| `proposito_aprendizaje` | Propósito de aprendizaje (proceso didáctico) |
| `introduccion` | Introducción / dinámica inicial |
| `desarrollo_contenidos` | Desarrollo de contenidos temáticos |
| `desarrollo_actividades` | Desarrollo de actividades prácticas |
| `evaluacion_formativa` | Evaluación formativa transversal |
| `retroalimentacion` | Retroalimentación transversal |
| `cierre` | Cierre de la sesión |
| `extension` | Actividad de extensión |
| `rubrica` | Rúbrica de evaluación (analítica u holística) en formato JSON |

La distribución de tiempos por momento didáctico se calcula automáticamente a partir de `duracion_total` y se inyecta como variables adicionales en la plantilla.

---

## Deploy

El backend está pensado para desplegarse en **Railway** y el frontend React en **Vercel**.

### Railway (Backend Flask)

1. Conectar el repositorio en [railway.app](https://railway.app).
2. Configurar la variable de entorno `API_KEY` en el dashboard de Railway.
3. Railway detecta automáticamente el proyecto Python con Poetry.

> **Nota sobre LibreOffice:** La conversión a PDF requiere `soffice`. En Railway es necesario configurar un buildpack que lo incluya, o evaluar una alternativa como [Gotenberg](https://gotenberg.dev).

---

## Flujo de trabajo Git

Este proyecto sigue **Git Flow** con `--no-ff` en todos los merges para mantener un historial narrativo y trazable.

### Convención de ramas

```
feature/descripcion-en-ingles   # Nueva funcionalidad
refactor/descripcion-en-ingles  # Reestructura o mejora de código
fix/descripcion-en-ingles       # Corrección de errores
docs/descripcion-en-ingles      # Documentación
chore/descripcion-en-ingles     # Configuración o mantenimiento
```

### Convención de commits (Conventional Commits)

```
feat: descripción      # Nueva funcionalidad
refactor: descripción  # Reestructura de código
fix: descripción       # Corrección de error
docs: descripción      # Documentación
chore: descripción     # Configuración o mantenimiento
```

### Merge a main

```bash
git checkout main
git merge --no-ff nombre-rama -m "tipo: descripción del merge"
git push origin main
```

---

## Autor

**Randolph Fabrizio Ramirez Palacios**
Institución Educativa Fe y Alegría 18 — Sullana, Perú
[GitHub](https://github.com/tu-usuario)
