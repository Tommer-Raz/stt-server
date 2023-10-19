from flask import Flask, abort, request
import whisper
import logging
from flasgger import Swagger
from tempfile import NamedTemporaryFile

# Load the Whisper model:
model = whisper.load_model('large-v2')

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "version": "1.0.0",
            "title": "Whisper API",
            "description": "API for transcribing and translating audio files with Whisper",
            "endpoint": 'v1_spec',
            "route": '/v1/spec'
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger = Swagger(app, config=swagger_config)

@app.route('/', methods=['POST'])
def handler():
    """
    File Upload API
    ---
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: The audio file to be transcribed or translated
      - name: language
        in: formData
        type: string
        required: false
        default: Hebrew
        description: The language of the audio file
      - name: task
        in: formData
        type: string
        required: false
        default: transcribe
        description: The task to perform, either transcribe or translate
      - name: beam_size
        in: formData
        type: integer
        required: false
        default: 5
        description: The beam size for transcription or translation
      - name: best_of
        in: formData
        type: integer
        required: false
        default: 5
        description: The best of for transcription or translation
      - name: temperature
        in: formData
        type: number
        required: false
        default: 0
        description: The temperature value for transcription or translation
      - name: patience
        in: formData
        type: number
        required: false
        default: 1.0
        description: The patience value for transcription or translation
    responses:
      200:
        description: Successfully transcribed the file
    """
    if not request.files:
        logger.error('No file part in the request')
        return {'error': 'No file part'}, 400

    language = request.form.get('language', 'Hebrew')
    task = request.form.get('task', 'transcribe')
    beam_size = int(request.form.get('beam_size', 5))
    best_of = int(request.form.get('best_of', 5))
    temperature = float(request.form.get('temperature', 0))
    patience = float(request.form.get('patience', 1.0))

    # Perform validation checks
    if task not in {'transcribe', 'translate'}:
        logger.error('Invalid task. Must be either transcribe or translate.')
        return {'error': 'Invalid task. Must be either transcribe or translate.'}, 400


    options = dict(language=language, task=task, beam_size=beam_size, best_of=best_of, temperature=temperature, patience=patience)
    # For each file, let's store the results in a list of dictionaries.
    results = []

    # Loop over every file that the user submitted.
    for filename, handle in request.files.items():
        try:
            # Create a temporary file
            temp = NamedTemporaryFile()
            # Write the uploaded file to the temporary file
            handle.save(temp)
            # Get the transcript of the temporary file
            result = model.transcribe(temp.name, **options)
            # Store the result object for this file
            # ...

        except Exception as e:
            logger.exception(f'An error occurred during transcription: {str(e)}')
            return {'error': f'An error occurred during transcription: {str(e)}'}, 500

        
        results.append({
            'filename': filename,
            'transcript': result['text'],
        })

    # This will be automatically converted to JSON.
    return {'results': results}