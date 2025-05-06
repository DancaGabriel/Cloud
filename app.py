from flask import Flask, render_template, request, jsonify
import requests
import os
import uuid # Pentru X-ClientTraceId

app = Flask(__name__)

# --- Configurare API Microsoft Translator ---
TRANSLATOR_API_KEY = os.environ.get('TRANSLATOR_API_KEY')
TRANSLATOR_API_ENDPOINT = os.environ.get('TRANSLATOR_API_ENDPOINT')
TRANSLATOR_API_REGION = os.environ.get('TRANSLATOR_API_REGION')

@app.route('/')
def home():
  return render_template('index.html') # Vom actualiza index.html mai jos

@app.route('/translate', methods=['POST'])
def translate_text_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body trebuie să fie JSON."}), 400

        text_to_translate = data.get('text')
        target_language = data.get('to', 'en') # Limba țintă implicită: engleză
        source_language = data.get('from', None) # Opțional, API-ul poate detecta limba sursă

        if not text_to_translate:
            return jsonify({"error": "Parametrul 'text' este obligatoriu."}), 400

        if not TRANSLATOR_API_KEY or not TRANSLATOR_API_ENDPOINT or not TRANSLATOR_API_REGION:
            app.logger.error("Variabilele de mediu pentru Translator API nu sunt configurate complet.")
            return jsonify({"error": "Serviciul de traducere nu este configurat corect pe server."}), 500

        headers = {
            'Ocp-Apim-Subscription-Key': TRANSLATOR_API_KEY,
            'Ocp-Apim-Subscription-Region': TRANSLATOR_API_REGION, # Necesar pentru Translator API
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4()) # ID unic pentru urmărirea cererii, bună practică
        }

        # Construiește URL-ul complet pentru operația de traducere
        # Asigură-te că endpoint-ul nu are / la sfârșit înainte de a adăuga calea
        constructed_url = TRANSLATOR_API_ENDPOINT.rstrip('/') + '/translate'
        
        params = {
            'api-version': '3.0',
            'to': target_language
        }
        if source_language:
            params['from'] = source_language

        # Corpul cererii trebuie să fie o listă de obiecte JSON, fiecare cu o cheie 'text'
        body = [{'text': text_to_translate}]

        response = requests.post(constructed_url, params=params, headers=headers, json=body)
        response.raise_for_status() # Ridică excepție pentru erori HTTP (4xx, 5xx)

        translation_response = response.json()
        
        # Extrage textul tradus
        # Răspunsul este o listă, corespunzătoare listei din body
        if translation_response and len(translation_response) > 0 and \
           translation_response[0].get('translations') and \
           len(translation_response[0]['translations']) > 0:
            translated_text = translation_response[0]['translations'][0]['text']
            detected_language = translation_response[0].get('detectedLanguage', {}).get('language', 'N/A')
            return jsonify({
                "translatedText": translated_text,
                "detectedLanguage": detected_language,
                "targetLanguage": target_language
            })
        else:
            app.logger.error(f"Răspuns neașteptat de la API Translator: {translation_response}")
            return jsonify({"error": "Nu s-a putut extrage traducerea din răspunsul API."}), 500

    except requests.exceptions.HTTPError as http_err:
        error_message = f"Eroare HTTP: {http_err}"
        status_code = http_err.response.status_code if http_err.response is not None else 500
        try:
            # Încercăm să obținem detalii din răspunsul API-ului, dacă e JSON
            error_details = http_err.response.json()
            if error_details.get("error") and error_details["error"].get("message"):
                error_message = f"Eroare API Translator: {error_details['error']['message']}"
        except ValueError: # Dacă răspunsul nu e JSON
            error_message = f"Eroare API Translator: {http_err.response.text}"
        app.logger.error(error_message)
        return jsonify({"error": error_message}), status_code
    except Exception as e:
        app.logger.error(f"O eroare neașteptată a apărut la traducere: {e}", exc_info=True)
        return jsonify({"error": f"O eroare neașteptată: {str(e)}"}), 500

if __name__ == '__main__':
    # Pentru rulare locală în dezvoltare, setează variabilele de mediu
    if not all([TRANSLATOR_API_KEY, TRANSLATOR_API_ENDPOINT, TRANSLATOR_API_REGION]):
        print("AVERTISMENT: Una sau mai multe variabile de mediu pentru Translator API nu sunt setate.")
        print("(TRANSLATOR_API_KEY, TRANSLATOR_API_ENDPOINT, TRANSLATOR_API_REGION)")
        print("Funcționalitatea de traducere nu va funcționa.")
    app.run(debug=False) # debug=False e recomandat pentru producție