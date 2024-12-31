from flask import Flask
from app.routes import main
import os

app = Flask(__name__)

# Set the secret key for sessions
app.secret_key = os.urandom(24)  # Generates a random secret key

# Registering the routes from routes.py
app.register_blueprint(main)

# Limiting the file size of uploads (e.g., 16MB)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

if __name__ == "__main__":
    app.run(host="192.168.29.55", port=5000, debug=True)
