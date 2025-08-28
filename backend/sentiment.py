"""
File: sentiment.py
Purpose: Performs sentiment analysis using the Hugging Face Transformers pipeline.

Flow:
- Text is sent to the /analyze endpoint in main.py.
- This file processes the text and returns the sentiment and confidence score.
"""

from transformers import pipeline

# Initialize the sentiment analysis pipeline
sentiment_pipeline = pipeline("sentiment-analysis")

def analyze_sentiment(text: str):
    """
    Analyze the sentiment of the given text.

    Args:
        text (str): The text to analyze.

    Returns:
        dict: A dictionary containing the sentiment ('positive' or 'negative') and the confidence score.
    """
    result = sentiment_pipeline(text)[0]
    sentiment = result["label"].lower()  # e.g., 'positive' or 'negative'
    confidence = round(result["score"], 2)
    return {"sentiment": sentiment, "confidence": confidence}
