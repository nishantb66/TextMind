import openai
import os

# Initialize OpenRouter client with your API key
openai.api_base = "https://openrouter.ai/api/v1"
openai.api_key = os.getenv(
    "OPENROUTER_API_KEY"
)  # Ensure the environment variable is set


# Function for general chat
def generate_chat(message):
    """
    Uses OpenRouter API to generate a chat response using an OpenAI model.
    """
    try:
        response = openai.ChatCompletion.create(
            model="meta-llama/llama-3.2-3b-instruct",  # Specify the model
            messages=[{"role": "user", "content": message}],
        )
        return response.choices[0].message["content"]

    except Exception as e:
        return {"error": str(e)}


# Function for querying a PDF using a language model
def query_pdf_with_llama(message, pdf_text):
    """
    Uses the OpenRouter API to query the uploaded PDF content using a LLaMA model.
    """
    # Combine the PDF content and user input into a prompt
    prompt = f"Based on the following document: {pdf_text}\n\nAnswer this question: {message}"

    try:
        # Call the OpenRouter API (using an OpenAI model like gpt-3.5-turbo or a llama variant)
        chat_completion = openai.ChatCompletion.create(
            messages=[{"role": "user", "content": prompt}],
            model="meta-llama/llama-3.2-3b-instruct",  # Adjust the model as needed
        )
        # Extract and return the response from the model
        return {"response": chat_completion.choices[0].message["content"]}

    except Exception as e:
        # If there's an error, return the error message
        return {"error": str(e)}
