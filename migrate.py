"""
migrate_missing.py — uploads only tables that don't yet exist in Supabase
Run: python migrate_missing.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set. Check your .env file.")

engine = create_engine(DATABASE_URL)

dat_folder = "data/"
files = {
    "Players.csv":                  "Players",
    "PlayerStatistics.csv":         "PlayerStatistics",
    "PlayerStatisticsAdvanced.csv": "PlayerStatisticsAdvanced",
    "PlayerStatisticsScoring.csv":  "PlayerStatisticsScoring",
    "Games.csv":                    "Games",
    "TeamHistories.csv":            "TeamHistories",
    "TeamStatistics.csv":           "TeamStatistics",
    "TeamStatisticsAdvanced.csv":   "TeamStatisticsAdvanced",
    "TeamStatisticsScoring.csv":    "TeamStatisticsScoring",
}

# check what's already in Supabase
existing = inspect(engine).get_table_names()
print(f"Tables already in Supabase: {existing}\n")

for filename, table_name in files.items():
    if table_name in existing:
        print(f"SKIP '{table_name}' — already exists")
        continue

    filepath = os.path.join(dat_folder, filename)
    if not os.path.exists(filepath):
        print(f"SKIP '{table_name}' — CSV file not found at {filepath}")
        continue

    print(f"Uploading {filename} → table '{table_name}'...")
    df = pd.read_csv(filepath, low_memory=False)
    with engine.begin() as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False, chunksize=500)
    print(f"  Done. {len(df):,} rows loaded.")

print("\nAll done.")