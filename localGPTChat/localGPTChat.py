import logging
import os
import shutil
import subprocess
import argparse
import requests
import tempfile

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, send, emit

from werkzeug.utils import secure_filename

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
app.secret_key = "LeafmanZSecretKey"

API_HOST = "http://localhost:5110/api"

@socketio.on("message")
def prompt_route(message):
    global QA
    user_prompt = message
    print(f"User Prompt: {user_prompt}")

    main_prompt_url = f"{API_HOST}/prompt_route"
    response = requests.post(main_prompt_url, data={"user_prompt": user_prompt})
    print(response.status_code)  # print HTTP response status code for debugging
    if response.status_code == 200:
        print(response.json())  # Print the JSON data from the response
        send(response.json(), broadcast=True)

# PAGES #
@app.route("/", methods=["GET", "POST"])
def home_page():
    if request.method == "POST":
        if "documents" in request.files:
            delete_source_url = f"{API_HOST}/delete_source"  # URL of the /api/delete_source endpoint
            if request.form.get("action") == "reset":
                response = requests.get(delete_source_url)
                if response.status_code == 200:
                    logging.info(f'Successfully deleted documents and context.')
            save_document_url = f"{API_HOST}/save_document"
            run_ingest_url = f"{API_HOST}/run_ingest"  # URL of the /api/run_ingest endpoint
            files = request.files.getlist("documents")
            print(len(files))
            # print(files)
            for file in files:
                logging.info(f'Adding file: {file.filename}')
                # print(file.filename)
                filename = secure_filename(file.filename)
                with tempfile.SpooledTemporaryFile() as f:
                    f.write(file.read())
                    f.seek(0)
                    response = requests.post(save_document_url, files={"document": (filename, f)})
                    if response.status_code == 200:
                        logging.info(f'{file.filename} successfully saved.')
                    elif response.status_code == 400:
                        logging.info(f'There was a bad request to the API when saving {file.filename}')
                    elif response.status_code == 500:
                        logging.info(f'There was an error saving {file.filename}')
                    # print(response.status_code)  # print HTTP response status code for debugging
            # Make a GET request to the /api/run_ingest endpoint
            response = requests.get(run_ingest_url)
            if response.status_code == 200:
                logging.info(f'Document(s) successfully ingested.')
            elif response.status_code == 500:
                logging.info('There was an error ingesting the document(s)')
            # print(response.status_code)  # print HTTP response status code for debugging
        elif request.form.get("action") == "reset":
            delete_source_url = f"{API_HOST}/delete_source"  # URL of the /api/delete_source endpoint
            response = requests.get(delete_source_url)
            if response.status_code == 200:
                logging.info(f'Successfully deleted documents and context.')
        else:
            logging.info(f'Request contains no documents to add.')
    # Display the form for GET request
    return render_template(
        "chat.html"
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5111, help="Port to run the API on. Defaults to 5111.")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to run the UI on. Defaults to 127.0.0.1. "
        "Set to 0.0.0.0 to make the UI externally "
        "accessible from other devices.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s", level=logging.INFO
    )
    
    # logging.info(f"Running on: {DEVICE_TYPE}")
    # print(f"Running on: {DEVICE_TYPE}")

    app.run(debug=False, host=args.host, port=args.port)