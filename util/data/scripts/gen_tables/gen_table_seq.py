import common.constants as const

import argparse
import os
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser('Generate dataframe pickle for sequential run from csv.')
    parser.add_argument('--csv',
                        default=os.path.join(const.DATA_HOME, 'csv/seq.csv'),
                        help='CSV file to parse')
    parser.add_argument('--output',
                        default=os.path.join(const.DATA_HOME, 'pickles/seq.pkl'),
                        help='Output path for the dataframe pickle')

    results = parser.parse_args()
    return results


# Parse arguments
args = parse_args()

# Read CSV file
# df = pd.read_csv(args.csv, index_col='pair_str')
df = pd.read_csv(args.csv)
df.sort_values('pair_str', inplace=True)

# TODO: process columns in seq df

# Output pickle
df.to_pickle(args.output)

