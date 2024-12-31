import os
from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
from app.openrouter_chat import generate_chat  # Correct import for chat function
from app.openrouter_chat import (
    query_pdf_with_llama,
)  # Assuming this is defined in a separate file now
from pdf_handler import (
    extract_text_from_pdf,
)  # Assuming this exists and extracts text from PDFs

main = Blueprint("main", __name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}

# Store the uploaded PDF's text in memory (temporary storage)
pdf_text = ""


# Utility function to check if the uploaded file is a PDF
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@main.route("/")
def home():
    return render_template("chatbot_index.html")


@main.route("/chat", methods=["POST"])
def chat():
    global pdf_text
    user_input = request.json.get("message")

    if user_input:
        # If a PDF has been uploaded, use the OpenRouter model to answer questions based on the PDF
        if pdf_text:
            response = query_pdf_with_llama(
                user_input, pdf_text
            )  # Calls PDF-based query method
            if "error" in response:
                return (
                    jsonify({"response": response["error"]}),
                    500,
                )  # Handle errors gracefully
            return jsonify({"response": response["response"]})
        else:
            # Fall back to general chat using OpenRouter
            response = generate_chat(user_input)
            return jsonify({"response": response})

    return jsonify({"response": "No input provided!"}), 400


@main.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    global pdf_text
    if "pdf" not in request.files:
        return jsonify({"error": "No file part in the request."}), 400

    file = request.files["pdf"]

    if file.filename == "":
        return jsonify({"error": "No file selected for uploading."}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # Ensure the uploads folder exists
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)  # Create the folder if it doesn't exist

        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Extract text from the uploaded PDF
        pdf_text = extract_text_from_pdf(file_path)

        return jsonify({"message": "PDF uploaded successfully."})

    return jsonify({"error": "Invalid file format. Only PDFs are allowed."}), 400


@main.route("/clear_pdf", methods=["POST"])
def clear_pdf():
    global pdf_text
    pdf_text = ""  # Clear the PDF content from memory
    return jsonify({"message": "PDF cleared successfully."})
