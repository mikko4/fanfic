import logging
import os
import time

import pandas as pd

from sentiment import get_emotion_scores
from utils import create_open, smooth_scores

# Set up logging configuration
fmt = f"%(filename)-20s:%(lineno)-4d %(asctime)s %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=fmt,
    handlers=[
        logging.StreamHandler(),  # Log to console
    ],
)


def split_text_into_percentiles(text: str, window_size=500, num_windows=100):
    words = text.split()
    total_words = len(words)

    if total_words > 50000:
        words = words[:50000]
        total_words = 50000

    if total_words <= 0:
        return []

    if total_words <= window_size:
        return [" ".join(words)]

    segment_size = (total_words - (window_size + 1)) / num_windows

    chunks = []
    for perc in range(1, num_windows + 1):
        start_point = int(segment_size * (perc - 1))
        end_point = start_point + window_size
        if end_point > total_words:
            end_point = total_words

        chunk_words = words[start_point:end_point]
        chunk_text = " ".join(chunk_words)
        chunks.append(chunk_text)

    return chunks


def process_transcripts(df, output_file, num_percentiles=100, save_interval=4):
    # Generate the summary file name automatically based on the output file
    summary_file = output_file.replace(".pkl", "_summary.pkl")

    # Load existing results if any
    if os.path.exists(output_file):
        existing_results = pd.read_pickle(output_file)
        processed_transcript_ids = set(existing_results["url"].unique())
        all_scores = existing_results.to_dict("records")  # Convert to list of dicts
        logging.info(f"Loaded existing results from {output_file}.")
    else:
        all_scores = []
        processed_transcript_ids = set()
        logging.info("No existing results found. Starting fresh.")

    # Load existing summary data if any
    if os.path.exists(summary_file):
        existing_summary = pd.read_pickle(summary_file)
        summary_scores = existing_summary.to_dict("records")  # Convert to list of dicts
        processed_summary_ids = set(existing_summary["url"].unique())
        logging.info(f"Loaded existing summary data from {summary_file}.")
    else:
        summary_scores = []
        processed_summary_ids = set()
        logging.info("No existing summary data found. Starting fresh.")

    total_transcripts = len(df)
    start_time = time.time()
    transcripts_processed = 0  # Counter for transcripts processed in this run

    for idx, (transcript_id, transcript_text) in enumerate(zip(df["url"], df["text"])):
        if not transcript_id or not transcript_text:
            continue

        current_time = time.time()

        if transcript_id in processed_transcript_ids:
            logging.info(f"Skipping transcript {transcript_id}, already processed.")
            continue

        # Split text into percentiles
        chunks = split_text_into_percentiles(
            transcript_text, window_size=500, num_windows=num_percentiles
        )

        percentile_scores = []
        for chunk in chunks:
            scores = get_emotion_scores(chunk)
            percentile_scores.append(scores)

        if not percentile_scores:
            continue

        # Smooth scores across percentiles
        smoothed_scores = {}
        for key in percentile_scores[0].keys():
            scores = [score[key] for score in percentile_scores if key in score]
            smoothed_scores[key] = smooth_scores(scores)

        # Append per-percentile smoothed scores to `all_scores`
        for i in range(len(smoothed_scores["pos"])):
            row = {"url": transcript_id, "percentile": i + 1}
            row.update({k: smoothed_scores[k][i] for k in smoothed_scores})
            all_scores.append(row)

        # Calculate average for each emotion across percentiles
        avg_emotions = {
            f"avg_{emotion}": sum(smoothed_scores[emotion])
            / len(smoothed_scores[emotion])
            for emotion in smoothed_scores
        }

        # Calculate variance for each emotion across percentiles
        var_emotions = {
            f"var_{emotion}": sum(
                (x - avg_emotions[f"avg_{emotion}"]) ** 2
                for x in smoothed_scores[emotion]
            )
            / len(smoothed_scores[emotion])
            for emotion in smoothed_scores
        }

        # Calculate the average of these variances across all emotions
        avg_variance_across_emotions = sum(var_emotions.values()) / len(var_emotions)

        # Create a row for the summary DataFrame
        summary_row = {"url": transcript_id}
        summary_row.update(avg_emotions)
        summary_row["avg_variance_across_emotions"] = avg_variance_across_emotions
        summary_scores.append(summary_row)

        # Increment the counter
        transcripts_processed += 1

        # Periodically save intermediate results
        if transcripts_processed % save_interval == 0:
            with create_open(output_file, "wb") as file:
                pd.DataFrame(all_scores).to_pickle(file)
                logging.info(f"Saved intermediate results to {output_file}.")

            with create_open(summary_file, "wb") as file:
                pd.DataFrame(summary_scores).to_pickle(file)
                logging.info(f"Saved intermediate summary to {summary_file}.")

        # Log progress
        transcripts_remaining = total_transcripts - idx - 1
        avg_time_per_transcript = (current_time - start_time) / (idx + 1)

        logging.info(
            f"Processed {idx + 1}/{total_transcripts} transcripts. "
            f"{transcripts_remaining} remaining. "
            f"Average time per transcript: {avg_time_per_transcript:.2f} seconds."
        )

    # Save final results
    pd.DataFrame(all_scores).to_pickle(output_file)
    pd.DataFrame(summary_scores).to_pickle(summary_file)
    logging.info(
        f"Processing complete. Final results saved to {output_file} and summary saved to {summary_file}."
    )

    return pd.DataFrame(all_scores), pd.DataFrame(summary_scores)
