import os
import requests
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from dotenv import load_dotenv
from groq import Groq
from bs4 import BeautifulSoup

app = Flask(__name__)

# Set upload folder and allowed file types
app.config["UPLOAD_FOLDER"] = "uploads/"
# app.config["ALLOWED_EXTENSIONS"] = {"pdf"}

# Configure session to use filesystem
app.config["SECRET_KEY"] = (
    "b'\xf1\xc9\xd2\xab\x86\xf7\xd0\x87\x12\x9c\xd1\x8e\x93\xe3\xff\xc4\x84\x98\xa3\xe4\xf7\xd4'"
)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Load .env file
load_dotenv()

# Initialize the Groq client
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

# Store user interactions for admin view
interaction_data = []


# Function to fetch content from a news article link
def fetch_news_article_content(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            # Extract main content from the article
            article_text = " ".join(p.get_text() for p in soup.find_all("p"))
            return article_text
        else:
            return None
    except Exception as e:
        return None


# Home page
@app.route("/")
def index():
    return render_template("news_chat.html")


# Admin page to view user questions and news article information
@app.route("/admin")
def admin_page():
    return render_template("news_chatbot_admin.html", interaction_data=interaction_data)


# Route to handle single news article link input and text extraction for chatting
@app.route("/upload_single", methods=["POST"])
def upload_single_news_link():
    article_url = request.form.get("url")
    if not article_url:
        return jsonify({"error": "No URL provided"})

    # Fetch content from the provided URL
    article_content = fetch_news_article_content(article_url)

    if not article_content:
        return jsonify({"error": "Failed to retrieve content from the article"})

    # Store article info in session
    session["single_article_content"] = article_content
    interaction_data.append({"type": "single_news_article", "url": article_url})

    return jsonify(
        {
            "message": "Article content loaded successfully!",
            "text": article_content[:500] + "...",  # Preview first 500 characters
        }
    )


# Route to handle chat interaction for a single article
@app.route("/ask_single", methods=["POST"])
def ask_single():
    query = request.form["query"]
    article_content = session.get("single_article_content", "")

    if not article_content:
        return jsonify({"error": "No article content to query"})

    # Combine the query and the extracted article content for the model to process
    prompt = f"Based on the following article content: {article_content}\n\nAnswer this question: {query}"

    # Send query to the model
    response = query_llama(prompt)

    # Store the question and answer in interaction_data
    interaction_data.append(
        {"type": "question_answer", "input": query, "output": response["response"]}
    )

    return jsonify(response)


# Route to handle multiple news article link input and text extraction for comparison
@app.route("/upload_multiple", methods=["POST"])
def upload_news_link_multiple():
    article_urls = request.form.getlist("urls[]")
    if not article_urls or len(article_urls) < 2:
        return jsonify(
            {"error": "Please provide at least two article URLs for comparison."}
        )

    article_contents = []
    for url in article_urls:
        article_content = fetch_news_article_content(url)
        if not article_content:
            return jsonify(
                {"error": f"Failed to retrieve content from the article at {url}"}
            )
        article_contents.append({"url": url, "content": article_content})

    # Store article info in session
    session["article_contents"] = article_contents
    interaction_data.append({"type": "news_articles", "urls": article_urls})

    return jsonify({"message": "Article contents loaded successfully!"})


# Route to handle comparison and conclusion for multiple articles
@app.route("/compare", methods=["POST"])
def compare_articles():
    article_contents = session.get("article_contents", [])

    if len(article_contents) < 2:
        return jsonify({"error": "Not enough articles to compare."})

    # Send article contents for comparison to Groq Llama model
    prompt = "Compare the following articles and provide a conclusion about which article presents better information:\n"
    for i, article in enumerate(article_contents):
        prompt += f"Article {i + 1} (URL: {article['url']}):\n{article['content'][:500]}...\n\n"

    response = query_llama(prompt)

    # Store the comparison and conclusion in interaction_data
    interaction_data.append(
        {
            "type": "comparison",
            "articles": article_contents,
            "conclusion": response["response"],
        }
    )

    return jsonify(response)


# Function to query the Llama model via Groq API
def query_llama(text):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": text,
                }
            ],
            model="llama3-8b-8192",  # Replace with the appropriate model from Groq
        )
        return {"response": chat_completion.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    app.run(host="192.168.29.55", port=8000, debug=True)
