from flask import Flask, request, jsonify
from flask_cors import CORS  # para evitar problemas de CORS
from ai_doc import generate_document

################################################################

app = Flask(__name__)

CORS(app)  # Habilita CORS para la aplicación Flask

# Habilita CORS en todos los rutas/endpoints y para todos los dominios y métodos.
# CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/')
def index():
    return "API de Flask está funcionando!"


@app.route('/generate-document', methods=["POST"])

def generate_document_endpoint():

    data = request.get_json()
    user_input = data.get('user_input')
    docx_path, pdf_path = generate_document(user_input)

    return jsonify(success=True, pdf_path=pdf_path, docx_path=docx_path)

if __name__ == '__main__':
    app.run()
