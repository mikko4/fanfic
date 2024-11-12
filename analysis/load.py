import pandas as pd
import numpy as np
import zipfile
import os
import re
from utils import create_open

# Define base directory paths
base_dir = "/scratch/tripakis.m/data-research/fanfic/scraped/"  # Directory containing the folders or ZIP files
output_base_dir = (
    "/scratch/tripakis.m/data-research/fanfic/splits/"  # Directory to save split files
)

# Ensure the output base directory exists
os.makedirs(output_base_dir, exist_ok=True)

# Define a regular expression pattern to match names like "03.21-09.21 Mikko Tripakis"
pattern = re.compile(r"\d{2}\.\d{2}-\d{2}\.\d{2} Mikko Tripakis(\.zip)?$")


# Function to split and save DataFrame and print stats
def split_and_save(df, output_dir, num_splits=40):
    # Split the data into parts
    df_splits = np.array_split(df, num_splits)
    stats = []

    # Save each part and collect statistics
    for i, df_part in enumerate(df_splits):
        part_filename = f"{output_dir}/fanfics_part_{i}.pkl"
        with create_open(part_filename, "wb") as file:
            df_part.to_pickle(file)

        # Collect stats for this part
        part_stats = {
            "part": i + 1,
            "fanfics_count": len(df_part),
            "filename": part_filename,
        }
        stats.append(part_stats)

    # Print statistics for the current ZIP/folder
    print(f"\nSaved {num_splits} parts to {output_dir}")
    for stat in stats:
        print(
            f"Part {stat['part']}: {stat['fanfics_count']} fanfics - saved to {stat['filename']}"
        )
    print(
        f"Total fanfics in this collection: {sum(s['fanfics_count'] for s in stats)}\n"
    )


# Loop through each entry in base_dir
for entry in os.listdir(base_dir):
    entry_path = os.path.join(base_dir, entry)
    if pattern.match(entry):  # Only process entries matching the pattern

        # Set up directory for output specific to this ZIP or folder
        entry_output_dir = os.path.join(
            output_base_dir, entry.replace(".zip", "").replace(" Mikko Tripakis", "")
        )
        os.makedirs(entry_output_dir, exist_ok=True)

        # Initialize an empty DataFrame for this ZIP/folder
        all_data = pd.DataFrame()

        # Check if the entry is a ZIP file
        if entry.endswith(".zip"):
            with zipfile.ZipFile(entry_path, "r") as zip_file:
                for csv_filename in zip_file.namelist():
                    if csv_filename.endswith(".csv"):
                        with zip_file.open(csv_filename) as csv_file:
                            df = pd.read_csv(csv_file)
                            all_data = pd.concat([all_data, df], ignore_index=True)

        # If it's a folder, read CSVs directly from the folder
        elif os.path.isdir(entry_path):
            for csv_filename in os.listdir(entry_path):
                if csv_filename.endswith(".csv"):
                    csv_path = os.path.join(entry_path, csv_filename)
                    df = pd.read_csv(csv_path)
                    all_data = pd.concat([all_data, df], ignore_index=True)

        # Split, save, and print stats
        split_and_save(all_data, entry_output_dir)
