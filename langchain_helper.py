import os
import requests
from langchain.prompts import PromptTemplate


# Function to query Groq API using Llama model
def query_llama_via_groq(prompt_text):
    API_KEY = os.getenv("GROQ_API_KEY")
    API_URL = "https://api.groq.com/llama/v3"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "prompt": prompt_text,
        "max_tokens": 150,
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["text"]
        else:
            print(f"Error from Groq API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception during Groq API request: {e}")
        return None


# Function to create a prompt with Langchain and query the Groq API
def create_prompt_and_query(article_text, user_query):
    # Update template to reflect that we're working with a news article instead of a PDF document
    template = "Based on the following news article: {document_text}\n\nAnswer this question: {query}"

    # Langchain PromptTemplate
    prompt_template = PromptTemplate(
        input_variables=["document_text", "query"], template=template
    )

    # Format the prompt using Langchain
    formatted_prompt = prompt_template.format(
        document_text=article_text, query=user_query
    )

    # Query Groq API using the formatted prompt
    return query_llama_via_groq(formatted_prompt)
