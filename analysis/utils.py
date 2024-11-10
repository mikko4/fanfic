import re
import numpy as np
import os


def create_open(path: str, mode: str = "r", **kwargs):

    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, mode=mode, **kwargs)


def merge_transcripts(
    df,
    transcript_id_col="url",
    component_order_col="componentorder",
    text_col="componenttext",
):
    # drop null rows
    df.dropna(inplace=True)

    # Sort by transcript_id and component_order to preserve the correct order of components
    df_sorted = df.sort_values([transcript_id_col, component_order_col])

    # Group by transcript_id and concatenate the text components for each transcript
    df_merged = (
        df_sorted.groupby(transcript_id_col)
        .agg(
            {text_col: " ".join}  # Concatenate text components with a space in between
        )
        .reset_index()
    )

    return df_merged


def split_text_into_chunks(text):
    return re.sub("<[^>]+>", "", str(text)).split(". ")


def smooth_scores(scores):
    scores = np.array(scores)
    if len(scores) == 0:
        return []
    elif len(scores) == 1:
        return scores.tolist()
    else:
        # Apply convolution with a window size of 3 for smoothing
        smoothed_scores = np.convolve(scores, np.ones(3) / 3, mode="same")
        # Handle the edges separately
        smoothed_scores[0] = (scores[0] + scores[1]) / 2
        smoothed_scores[-1] = (scores[-2] + scores[-1]) / 2
        return smoothed_scores.tolist()
