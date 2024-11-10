import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from utils import split_text_into_chunks

tokenizer = AutoTokenizer.from_pretrained(
    "SamLowe/roberta-base-go_emotions", clean_up_tokenization_spaces=True
)

model = AutoModelForSequenceClassification.from_pretrained(
    "SamLowe/roberta-base-go_emotions",
)
labels = [model.config.id2label[i] for i in range(28)]

sia = SentimentIntensityAnalyzer()


def score_emotions(text_list):
    try:
        # Batch processing the text list
        inputs = tokenizer(
            text_list, padding=True, truncation=True, return_tensors="pt"
        )
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits  # Shape: (batch_size, num_labels)
            # Apply sigmoid function and move logits back to CPU
            scores = torch.sigmoid(logits).numpy()

        return scores  # Return the array directly

    except Exception as e:
        # In case of exception, return NaNs
        num_chunks = len(text_list)
        num_labels = len(labels)
        return np.full((num_chunks, num_labels), np.nan)


def get_emotion_scores(text, noOvTag=False):
    vader_scores = sia.polarity_scores(text)
    combined_scores = {"pos_noOv" if noOvTag else "pos": vader_scores["pos"]}

    text_chunks = split_text_into_chunks(text)
    scores_array = score_emotions(
        text_chunks
    )  # Now an array of shape (num_chunks, num_labels)

    if scores_array.size > 0:
        # Compute mean over chunks
        emotion_means = np.mean(scores_array, axis=0)

        if not noOvTag:
            emotion_scores = dict(zip(labels, emotion_means))
        else:
            emotion_scores = {
                f"{label}_noOv": mean_score
                for label, mean_score in zip(labels, emotion_means)
            }

        combined_scores.update(emotion_scores)

    return combined_scores
