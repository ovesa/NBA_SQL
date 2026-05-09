# Explore the structure of the NBA database and its tables, including column names and data types.

import sqlite3

###############################################
######### Connection to SQL Database ##########
###############################################

# open connection to nba.db database file
# cursor object allows you to execute SQL queries and fetch results
conn = sqlite3.connect("nba.db")
cursor = conn.cursor()

# table names in the database
tables = [
    "Players",
    "PlayerStatistics",
    "PlayerStatisticsAdvanced",
    "PlayerStatisticsScoring",
    "Games",
    "TeamHistories",
    "TeamStatistics",
    "TeamStatisticsAdvanced",
    "TeamStatisticsScoring",
]

###############################################
####### Metadata Information Retrieval ########
###############################################

# return metadata about the tables in the database, including column names and data types
for table in tables:
    print(f"\n{'=' * 50}")
    print(f"TABLE: {table}")
    print("=" * 50)
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

conn.close()
