from flask import Flask, render_template
import os
import logging 
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError

app = Flask(__name__)
CONTAINER_NAME = "uploads"


logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    connection_status = "N/A"
    error_message = None
    connect_str = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')

    if not connect_str:
        connection_status = "Eroare"
        error_message = "Variabila de mediu AZURE_STORAGE_CONNECTION_STRING nu este setată."
        app.logger.error(error_message) # Loghează eroarea
    else:
        try:
            app.logger.info(f"Încercare conectare la containerul '{CONTAINER_NAME}'...")
            blob_service_client = BlobServiceClient.from_connection_string(connect_str)
            container_client = blob_service_client.get_container_client(CONTAINER_NAME)
            # Încearcă să obții prima pagină de blob-uri pentru verificare
            next(container_client.list_blobs(results_per_page=1).by_page())
            connection_status = f"Succes! Conectat la containerul '{CONTAINER_NAME}'."
            app.logger.info(connection_status) # Loghează succesul
        except StopIteration:
             connection_status = f"Succes! Conectat la containerul '{CONTAINER_NAME}' (gol sau prima pagină goală)."
             app.logger.info(connection_status) # Loghează succesul (container gol)
        except ClientAuthenticationError as e:
            connection_status = "Eroare Autentificare"
            error_message = "Verifică corectitudinea AZURE_STORAGE_CONNECTION_STRING."
            app.logger.error(f"{connection_status}: {error_message} - {e}") # Loghează eroarea
        except ResourceNotFoundError as e:
            connection_status = "Eroare"
            error_message = f"Containerul '{CONTAINER_NAME}' nu a fost găsit sau nu există acces."
            app.logger.error(f"{connection_status}: {error_message} - {e}") # Loghează eroarea
        except Exception as e:
            connection_status = "Eroare Necunoscută"
            error_message = f"A apărut o eroare neașteptată: {str(e)}"
            app.logger.error(f"{connection_status}: {error_message}") # Loghează eroarea


    return render_template('index.html',
                           blob_connection_status=connection_status,
                           blob_error_message=error_message)

