# Configuration file to setup this SQL project
# This project is designed to help me practice my SQL skills and learn how to use SQL through python
# Using the Kaggle dataset "NBA Database (1947 -- Present" (https://www.kaggle.com/datasets/eoinamoore/historical-nba-data-and-player-box-scores)
# Run python3 setup.py to load the CSV files into the SQLite database

import sqlite3
import pandas as pd
import os

####################################################
############# Directory and File Paths #############
####################################################

dat_folder = "data/"
db_name = "nba.db"

# files and corresponding table names in the database
# might not use all of these tables, but will keep just in case
files = {
    "Players.csv": "Players",
    "PlayerStatistics.csv": "PlayerStatistics",
    "PlayerStatisticsAdvanced.csv": "PlayerStatisticsAdvanced",
    "PlayerStatisticsScoring.csv": "PlayerStatisticsScoring",
    "Games.csv": "Games",
    "TeamHistories.csv": "TeamHistories",
    "TeamStatistics.csv": "TeamStatistics",
    "TeamStatisticsAdvanced.csv": "TeamStatisticsAdvanced",
    "TeamStatisticsScoring.csv": "TeamStatisticsScoring",
}


# Load CSVs into SQLite database
# cursor object allows you to execute SQL queries and fetch results
conn = sqlite3.connect(db_name)

for filename, table_name in files.items():
    filepath = os.path.join(dat_folder, filename)
    print(f"Loading {filename}: table '{table_name}'...")
    df = pd.read_csv(filepath, low_memory=False)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"Done. {len(df):,} rows loaded.")

conn.close()

print(f"{db_name} is ready.")
