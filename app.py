from flask import Flask, render_template, request 
import os
import uuid 
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError
import logging 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
TARGET_CONTAINER_NAME = "imagini" 

@app.route('/', methods=['GET', 'POST'])
def home():
    upload_message = None 

    if request.method == 'POST':
        if not CONNECTION_STRING:
            logger.error("Variabila de mediu AZURE_STORAGE_CONNECTION_STRING nu este setată.")
            return render_template('index.html') 

        if 'file_to_upload' not in request.files:
            logger.warning("Request POST primit fără 'file_to_upload'.")
            return render_template('index.html')

        file = request.files['file_to_upload']

        if file.filename == '':
            logger.warning("Request POST primit cu 'file_to_upload', dar fără nume de fișier (probabil nu s-a selectat).")
            return render_template('index.html')

        if file:
            try:
                blob_name = str(uuid.uuid4()) + "_" + file.filename
                logger.info(f"Încercare upload: {blob_name} în {TARGET_CONTAINER_NAME}")

                blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
                blob_client = blob_service_client.get_blob_client(container=TARGET_CONTAINER_NAME, blob=blob_name)
                
                blob_client.upload_blob(file.read(), blob_type="BlockBlob") 

                logger.info(f"SUCCES Upload: {blob_name}")

            except AzureError as e:
                logger.error(f"EROARE Azure la upload: {e}")
            except Exception as e:
                logger.error(f"EROARE Generală la upload: {e}")

            return render_template('index.html')

    return render_template('index.html')

