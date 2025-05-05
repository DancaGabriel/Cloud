import os
from flask import Flask, render_template, request, redirect, url_for
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)


connect_str = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
container_name = "uploads" 

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if not connect_str:
        print("EROARE: Stringul de conexiune Azure (AZURE_STORAGE_CONNECTION_STRING) nu este setat.")
        return "Eroare de configurare server.", 500

    if 'file' not in request.files:
        print("EROARE: Niciun 'file' în request.files.")
        return redirect(url_for('home'))

    file = request.files['file']

    if file.filename == '':
        print("EROARE: Nume de fișier gol.")
        return redirect(url_for('home'))

    filename = file.filename

    try:
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=filename)

        print(f"Încărcare fișier: {filename} în container: {container_name}")
        blob_client.upload_blob(file.stream, overwrite=True)
        print("Încărcare reușită!")

    except Exception as e:
        print(f"EROARE la încărcare: {e}")
        return f"A apărut o eroare la încărcare: {e}", 500

    return redirect(url_for('home'))