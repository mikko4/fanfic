import sys

import pandas as pd

from process import process_transcripts

if __name__ == "__main__":
    # Get the part number from command line arguments
    if len(sys.argv) != 3:
        print("Usage: python worker.py [year-range] [part_num]")
        sys.exit(-1)

    year = sys.argv[1]
    part_number = sys.argv[2]

    # Load the DataFrame part
    df = pd.read_pickle(f"splits/{year}/fanfics_part_{part_number}.pkl")

    # Process the DataFrame
    result_df = process_transcripts(
        df, output_file=f"results/{year}/result_part_{part_number}.pkl"
    )
    sys.exit(0)
