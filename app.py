from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for,
    send_file,
    make_response,
)
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline,
    AutoModelForTokenClassification,
    AutoModelForSeq2SeqLM,
)
from model import load_summarization_model, summarize_large_text
from newspaper import Article
from gensim import corpora, models
import spacy
import nltk
from nltk.corpus import stopwords
import pandas as pd
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from waitress import serve
import json
import os
import csv
from io import StringIO
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import tempfile
from flask_socketio import SocketIO

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a secure secret key

# Initialize logger
logging.basicConfig(level=logging.INFO)

# Initialize SocketIO
socketio = SocketIO(app, async_mode="gevent")

# Visit counter
visit_counts = {"home": 0}
prompt_counts = {"chatbot_prompts": 0}

# Load models and tokenizers for various functionalities
emotion_model_name = "j-hartmann/emotion-english-distilroberta-base"
emotion_tokenizer = AutoTokenizer.from_pretrained(emotion_model_name)
emotion_model = AutoModelForSequenceClassification.from_pretrained(emotion_model_name)

# Load pipelines
emotion_pipeline = pipeline(
    "text-classification",
    model=emotion_model,
    tokenizer=emotion_tokenizer,
    return_all_scores=True,
    truncation=True,
    max_length=512,
)
sentiment_pipeline = pipeline("sentiment-analysis")

# Emotion to Sentiment Mapping
emotion_to_sentiment = {
    "joy": "positive",
    "love": "positive",
    "optimism": "positive",
    "admiration": "positive",
    "approval": "positive",
    "gratitude": "positive",
    "pride": "positive",
    "anger": "negative",
    "disgust": "negative",
    "fear": "negative",
    "sadness": "negative",
    "guilt": "negative",
    "remorse": "negative",
    "annoyance": "negative",
    "surprise": "neutral",
    "realization": "neutral",
    "neutral": "neutral",
}


# Function to create sentiment summary
def summarize_sentiment(emotions):
    sentiment_summary = {"positive": 0, "negative": 0, "neutral": 0}
    for emotion, score in emotions.items():
        sentiment = emotion_to_sentiment.get(emotion.lower(), "neutral")
        sentiment_summary[sentiment] += score
    return sentiment_summary


def plot_sentiment_pie(sentiment_summary):
    labels = sentiment_summary.keys()
    sizes = sentiment_summary.values()
    colors = [
        "#4CAF50",
        "#F44336",
        "#FFC107",
    ]  # green, red, yellow for positive, negative, neutral
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors, startangle=140)
    plt.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Save pie chart to a temporary file
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, "sentiment_pie_chart.png")
    plt.savefig(file_path)
    plt.close()  # Close the plot to free memory

    return file_path


# Load advanced NER model
ner_model_name = "dbmdz/bert-large-cased-finetuned-conll03-english"
ner_tokenizer = AutoTokenizer.from_pretrained(ner_model_name)
ner_model = AutoModelForTokenClassification.from_pretrained(ner_model_name)
ner_pipeline = pipeline(
    "ner", model=ner_model, tokenizer=ner_tokenizer, aggregation_strategy="simple"
)
summarizer = load_summarization_model()

# Load spaCy model for additional NLP tasks
nlp = spacy.load("en_core_web_sm")

nltk.download("stopwords")
stop_words = stopwords.words("english")

# Load translation model
model_name = "facebook/m2m100_418M"
tokenizer = AutoTokenizer.from_pretrained(model_name)
translation_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

supported_languages = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "hi": "Hindi",
    "es": "Spanish",
    "it": "Italian",
    # Add more language codes and their names as needed
}


def preprocess(text):
    doc = nlp(text)
    return [
        token.lemma_.lower()
        for token in doc
        if not token.is_stop and not token.is_punct
    ]


def get_topic_interpretation(topic):
    terms = topic.split("+")
    main_terms = [term.split("*")[1].replace('"', "") for term in terms[:3]]
    return ", ".join(main_terms)


# Function to fetch article content from URL
def fetch_article_content(url):
    article = Article(url)
    article.download()
    article.parse()
    return article.text


# Load data
def load_data(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()
    questions, answers = [], []
    for line in lines:
        if line.startswith("Q:"):
            questions.append(line[3:].strip())
        elif line.startswith("A:"):
            answers.append(
                line[3:].strip().replace("\\n", "\n")
            )  # Convert \n back to newlines
    return pd.DataFrame({"question": questions, "answer": answers})


# Load dialogs.txt data
df = load_data("data/dialogs2.txt")

# Load sentence transformer model
sentence_model = SentenceTransformer("all-mpnet-base-v2")

# Generate embeddings for all questions
question_embeddings = sentence_model.encode(
    df["question"].tolist(), convert_to_tensor=True
)

# Save the embeddings and data
with open("embeddings.pkl", "wb") as emb_file:
    pickle.dump(question_embeddings, emb_file)

with open("faq_data.pkl", "wb") as data_file:
    pickle.dump(df, data_file)

# Load the embeddings, FAQ data, and sentence transformer model
with open("embeddings.pkl", "rb") as emb_file:
    question_embeddings = pickle.load(emb_file)

with open("faq_data.pkl", "rb") as data_file:
    faq_data = pickle.load(data_file)

model = SentenceTransformer("all-mpnet-base-v2")


@app.before_request
def before_request():
    if request.endpoint == "home":
        visit_counts["home"] += 1


@app.after_request
def after_request(response):
    if request.endpoint == "home":
        app.logger.info(
            f"Endpoint '/home' has been visited {visit_counts['home']} times."
        )
    return response


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    # Replace these with secure checks
    if username == "admin" and password == "admin1234":
        session["logged_in"] = True
        return jsonify({"success": True})
    else:
        return jsonify({"success": False})


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("logged_in", None)
    session.pop("authenticated", None)
    return jsonify({"success": True})


@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/home")
def home():
    return render_template("combined_index.html")


@app.route("/contributor")
def contributor():
    return render_template("contributors.html")


@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")


@app.route("/admin")
def admin():
    if "logged_in" not in session:
        return redirect(url_for("chatbot"))
    return render_template("admin.html")


# Mock user credentials for authentication
users = {"admin": "admin1234", "user": "password"}

# File to store persistent data
DATA_FILE = "data_storage.json"

# Placeholder for storing data
data_storage = []


def load_data_storage():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return []


def save_data_storage():
    with open(DATA_FILE, "w") as file:
        json.dump(data_storage, file)


data_storage = load_data_storage()


@app.route("/authenticate_user", methods=["POST"])
def authenticate_user():
    data = request.get_json()
    username = data.get("username")
    with open("users.json", "r") as user_file:
        users = json.load(user_file)
    if username in users:
        session["authenticated"] = True
        return jsonify({"success": True})
    else:
        return jsonify({"success": False})


@app.route("/authenticate_admin", methods=["POST"])
def authenticate_admin():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if username == "admin" and password == "admin1234":
        session["logged_in"] = True
        session["authenticated"] = True
        session["is_admin"] = True
        return jsonify({"success": True})
    else:
        return jsonify({"success": False})


# Load user data from users.json
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as user_file:
            return json.load(user_file)
    return []


def save_users(users):
    with open("users.json", "w") as user_file:
        json.dump(users, user_file)


# Fetch user data endpoint
@app.route("/get_user_data", methods=["GET"])
def get_user_data():
    users = load_users()
    return jsonify(users)


# Signup user and update user data
@app.route("/signup_user", methods=["POST"])
def signup_user():
    data = request.get_json()
    new_username = data.get("newUsername")
    users = load_users()
    if new_username in users:
        return jsonify({"success": False, "message": "Username already exists"})
    users.append(new_username)
    save_users(users)
    session["authenticated"] = True
    return jsonify({"success": True})


@app.route("/info_panel")
def info_panel():
    if not session.get("authenticated"):
        return redirect(url_for("welcome"))
    return render_template("info_panel.html")


@app.route("/logout_info", methods=["POST"])
def logout_info():
    session.pop("authenticated", None)
    return jsonify({"success": True})


@app.route("/get_data")
def get_data():
    if not session.get("authenticated"):
        return redirect(url_for("welcome"))
    return jsonify(data_storage)


@app.route("/clear_data", methods=["POST"])
def clear_data():
    if not session.get("authenticated"):
        return jsonify({"success": False}), 401
    data_storage.clear()
    save_data_storage()
    return jsonify({"success": True})


@app.route("/summarize", methods=["POST"])
def summarize():
    url = request.form["url"]
    try:
        # Fetch article content
        content = fetch_article_content(url)
        # Summarize content
        summary = summarize_large_text(summarizer, content)
        entry = {"type": "summarization", "input": url, "output": summary}
        data_storage.append(entry)
        save_data_storage()
    except Exception as e:
        summary = f"Error fetching or summarizing article: {str(e)}"
    return render_template("news_result.html", summary=summary, url=url)


@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    text = data["text"]

    # Emotion Detection
    emotion_results = emotion_pipeline(text)
    emotion_response = {
        emotion["label"]: emotion["score"]
        for result in emotion_results
        for emotion in result
    }

    # Summarize the overall sentiment (positive, negative, neutral)
    sentiment_summary = summarize_sentiment(emotion_response)

    # Generate pie chart and get the file path
    pie_chart_path = plot_sentiment_pie(sentiment_summary)
    pie_chart_filename = os.path.basename(pie_chart_path)

    # Store user input and emotion analysis results in data storage
    entry = {"type": "emotion_analysis", "input": text, "output": emotion_response}
    data_storage.append(entry)
    save_data_storage()  # Ensure the data is persisted

    response = {
        "emotions": emotion_response,
        "sentiment_summary": sentiment_summary,
        "pie_chart_url": f"/sentiment_pie_chart/{pie_chart_filename}",
    }
    return jsonify(response)


@app.route("/sentiment_pie_chart/<filename>")
def sentiment_pie_chart(filename):
    file_path = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="image/png")
    return "File not found", 404


@app.route("/ner", methods=["POST"])
def ner():
    data = request.json
    text = data["text"]
    ner_results = ner_pipeline(text)
    entities = [(ent["word"], ent["entity_group"]) for ent in ner_results]
    return jsonify({"entities": entities})


@app.route("/topic_modeling", methods=["POST"])
def topic_modeling():
    data = request.json
    text = data["text"]
    tokens = preprocess(text)
    # Create dictionary and corpus
    dictionary = corpora.Dictionary([tokens])
    corpus = [dictionary.doc2bow(tokens)]
    # Create LDA model
    lda_model = models.LdaModel(corpus, num_topics=1, id2word=dictionary, passes=10)
    # Extract topics
    topics = lda_model.print_topics(num_words=5)
    topics = [topic[1] for topic in topics]
    return jsonify({"topics": topics})


@app.route("/topic_modeling_combined", methods=["POST"])
def topic_modeling_combined():
    data = request.json
    text = data["text"]
    tokens = preprocess(text)
    # Create dictionary and corpus
    dictionary = corpora.Dictionary([tokens])
    corpus = [dictionary.doc2bow(tokens)]
    # Create LDA model
    lda_model = models.LdaModel(corpus, num_topics=1, id2word=dictionary, passes=10)
    # Extract topics
    topics = lda_model.print_topics(num_words=5)
    topics = [topic[1] for topic in topics]
    return jsonify({"topics": topics})


@app.route("/get_feedback")
def get_feedback():
    feedback_list = []
    if os.path.exists("feedback.txt"):
        with open("feedback.txt", "r") as file:
            feedback_list = file.readlines()
    return jsonify(feedback_list)


@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    data = request.json
    feedback = data.get("feedback", "")
    if not feedback:
        return jsonify({"error": "Feedback cannot be empty"}), 400
    try:
        with open("feedback.txt", "a") as f:
            f.write(feedback + "\n")
        # Notify clients (real-time update)
        socketio.emit("new_feedback", feedback)
        return jsonify({"message": "Feedback received"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/translate", methods=["GET", "POST"])
def translate():
    if request.method == "POST":
        source_text = request.form["source_text"]
        target_lang = request.form["target_lang"]
        translated_text = translate_text(source_text, target_lang)
        entry = {"type": "translation", "input": source_text, "output": translated_text}
        data_storage.append(entry)
        save_data_storage()
        return render_template(
            "translate.html",
            translated_text=translated_text,
            source_text=source_text,
            target_lang=target_lang,
            supported_languages=supported_languages,
        )
    return render_template("translate.html", supported_languages=supported_languages)


def translate_text(text, target_lang):
    tokenizer.src_lang = "en"  # Assuming the source language is always English
    encoded_text = tokenizer(text, return_tensors="pt")
    generated_tokens = translation_model.generate(
        **encoded_text, forced_bos_token_id=tokenizer.get_lang_id(target_lang)
    )
    translated_text = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
    return translated_text[0]


@app.route("/download_data", methods=["GET"])
def download_data():
    if not session.get("authenticated"):
        return redirect(url_for("welcome"))
    # Convert data storage to CSV format
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["type", "input", "output"])
    for entry in data_storage:
        writer.writerow([entry["type"], entry["input"], entry["output"]])
    # Create a response with the CSV data
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=data_storage.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route("/generate_word_cloud", methods=["GET"])
def generate_word_cloud():
    if not session.get("authenticated"):
        return redirect(url_for("welcome"))

    # Combine all data into a single text
    combined_text = " ".join(
        [
            entry["input"]
            + " "
            + (
                entry["output"]
                if isinstance(entry["output"], str)
                else json.dumps(entry["output"])
            )
            for entry in data_storage
        ]
    )

    # Generate the word cloud
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(
        combined_text
    )

    # Save the word cloud to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        wordcloud.to_file(temp_file.name)
        temp_file.seek(0)
        return send_file(temp_file.name, mimetype="image/png")


@app.route("/get_feedback_sentiment", methods=["POST"])
def get_feedback_sentiment():
    data = request.json
    feedback = data.get("feedback", "")
    sentiment = sentiment_pipeline(feedback)
    return jsonify(sentiment)


if __name__ == "__main__":
    socketio.run(app, host="192.168.29.55", port=8080)
