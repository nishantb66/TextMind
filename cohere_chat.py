import cohere

# Initialize Cohere client with your API key
co = cohere.Client(api_key="ptRKVrxahhCo1WM7Xv1NnP1pX6WdcD6GWf3lE7w7")


def generate_chat(message):
    # Using the `generate` function for text generation with the Cohere API
    response = co.generate(
        model="command-xlarge-nightly",  # Use appropriate model name
        prompt=message,
        max_tokens=100,  # You can adjust this based on your needs
        temperature=0.6,
    )
    return response.generations[0].text  # Access the first generated response
