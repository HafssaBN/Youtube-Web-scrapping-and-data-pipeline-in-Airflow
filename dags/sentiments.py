# sentiments.py

from transformers import pipeline
import pandas as pd

# Load the sentiment analysis model once at the beginning
# You can specify a model if desired, e.g., "distilbert-base-uncased-finetuned-sst-2-english"
sentiment_model = pipeline("sentiment-analysis")

def analyze_sentiment(text_data):
    """
    Analyzes the sentiment of the provided text data.

    Parameters:
    - text_data (List[str]): A list of text strings (comments) to analyze.

    Returns:
    - List[Dict]: A list of dictionaries containing the sentiment label and score.
    """
    try:
        return sentiment_model(text_data)
    except Exception as e:
        print(f"Error during sentiment analysis: {e}")
        return []
