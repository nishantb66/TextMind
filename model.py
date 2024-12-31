from transformers import pipeline


def load_summarization_model():
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    return summarizer


def summarize_text(summarizer, text, max_length=150, min_length=30):
    try:
        summary = summarizer(
            text, max_length=max_length, min_length=min_length, do_sample=False
        )
        return summary[0]["summary_text"]
    except Exception as e:
        return f""


def split_into_chunks(text, max_chunk_size=512):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def summarize_large_text(
    summarizer, text, max_chunk_size=512, max_length=150, min_length=30
):
    chunks = split_into_chunks(text, max_chunk_size=max_chunk_size)
    summaries = [
        summarize_text(summarizer, chunk, max_length=max_length, min_length=min_length)
        for chunk in chunks
    ]
    return " ".join(summaries)
