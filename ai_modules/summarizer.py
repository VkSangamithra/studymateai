def summarize_text(text):

    # Split text into sentences
    sentences = text.split('.')

    # Take first 3 sentences
    summary = '. '.join(sentences[:3])

    return summary