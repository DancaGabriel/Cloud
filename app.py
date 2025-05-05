import os
from flask import Flask, render_template, request, redirect, url_for
from azure.storage.blob import BlobServiceClient, ContainerClient # Am adăugat ContainerClient
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError # Importăm excepții specifice

app = Flask(__name__)

connect_str = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
container_name = "uploads" # Numele containerului (bucket-ului) tău

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
        return redirect(url_for('home')) # Folosim url_for aici pentru redirect e OK

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

    except ResourceNotFoundError:
         # Prins dacă container_name nu există DELOC când se încearcă get_blob_client sau upload
         print(f"EROARE: Containerul '{container_name}' nu a fost găsit.")
         return f"Eroare: Containerul '{container_name}' nu a fost găsit.", 404
    except HttpResponseError as e:
         # Prinde erori de autentificare sau alte probleme HTTP de la Azure
         print(f"EROARE la încărcare (HTTP): {e}")
         return f"A apărut o eroare la încărcare: {e.message}", e.status_code
    except Exception as e:
        # Prinde alte erori neașteptate
        print(f"EROARE neașteptată la încărcare: {e}")
        return f"A apărut o eroare la încărcare: {e}", 500

    return redirect(url_for('home'))


@app.route('/db_check') # Păstrăm numele rutei sau îl putem schimba în /blob_check
def db_check():
    if not connect_str:
        return "Eroare: Variabila de mediu AZURE_STORAGE_CONNECTION_STRING nu este setată.", 500

    try:
        print(f"Încercare conectare la containerul Blob '{container_name}'...")
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_client = blob_service_client.get_container_client(container_name)

        # Încercăm să obținem proprietățile containerului.
        # Asta face un apel la Azure și verifică dacă containerul există și avem acces.
        properties = container_client.get_container_properties()

        print(f"Acces reușit la containerul '{properties.name}'.")
        return f"Conexiune/Acces la containerul Blob '{container_name}' reușită!", 200

    except ResourceNotFoundError:
        error_message = f"Eroare: Containerul Blob '{container_name}' nu a fost găsit."
        print(error_message)
        return error_message, 404
    except HttpResponseError as e:
        # Prinde erori cum ar fi cele de autentificare (403 Forbidden) etc.
        error_message = f"Eroare la accesarea containerului Blob '{container_name}': {e.message}"
        print(error_message)
        return error_message, e.status_code # Returnează codul de eroare HTTP real
    except Exception as e:
        error_message = f"A apărut o eroare neașteptată la verificarea containerului: {e}"
        print(error_message)
        return error_message, 500