from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
  """Funcție care returnează 'Hello World!'."""
  return 'Hello World!'


if __name__ == '__main__':
  app.run(debug=True)