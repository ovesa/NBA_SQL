# Extension of top_scorers.py to include all top scorers in NBA history, not just the top 10.

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from plot_style import set_plot_style

# Import custom plot styles
set_plot_style()

###############################################
######### Connection to SQL Database ##########
###############################################

# open connection to nba.db database file
conn = sqlite3.connect("nba.db")

###############################################
################## SQL Query ##################
###############################################

# Across all NBA players since the beginning, do taller, heavier players score more?
query = """
SELECT
    ps.firstName || ' ' || ps.lastName AS player_name,
    SUBSTR(ps.gameDateTimeEst, 1, 4) AS season_year,
    COUNT(ps.gameId) AS games_played,
    
    ROUND(AVG(ps.points), 1) AS avg_points,
    ROUND(AVG(ps.points) / NULLIF(AVG(ps.numMinutes), 0), 2) AS points_per_minute,
        
    p.heightInches as height_inches,
    p.bodyWeightLbs as weight_lbs,
    p.draftRound as draft_round,
    
    p.guard AS guard,
    p.forward AS forward,
    p.center AS center

FROM PlayerStatistics ps
JOIN Players p ON ps.personId = p.personId
WHERE ps.gameType = 'Regular Season' AND ps.points IS NOT NULL AND ps.numMinutes IS NOT NULL
GROUP BY player_name, season_year, p.heightInches, p.bodyWeightLbs, p.draftRound, p.guard, p.forward, p.center
HAVING games_played >= 20
ORDER BY avg_points DESC
"""

# Run query and load results into a dataframe
df = pd.read_sql_query(query, conn)
conn.close()

###############################################
################ Quick Analysis ###############
###############################################

# Results to table
print(f"Total player-seasons: {len(df)}")
print(f"Height range: {df['height_inches'].min()} - {df['height_inches'].max()} inches")
print(f"Weight range: {df['weight_lbs'].min()} - {df['weight_lbs'].max()} lbs")
print(f"Avg points range: {df['avg_points'].min()} - {df['avg_points'].max()}")
print(f"NaN heights: {df['height_inches'].isna().sum()}")
print(f"NaN weights: {df['weight_lbs'].isna().sum()}")
print("\nSample (top 10 scorers):")
print(
    df.head(10)[
        [
            "player_name",
            "season_year",
            "avg_points",
            "points_per_minute",
            "height_inches",
            "weight_lbs",
        ]
    ].to_string(index=False)
)

# drop NaN heights and weights
df_clean = df.dropna(subset=["height_inches", "weight_lbs"]).copy()

# create height bins
df_clean["height_bin"] = pd.cut(
    df_clean["height_inches"],
    bins=range(63, 95, 3),
    labels=[f"{h}-{h + 2}" for h in range(63, 92, 3)],
)

# weight bins
df_clean["weight_bin"] = pd.cut(
    df_clean["weight_lbs"],
    bins=range(140, 340, 20),
    labels=[f"{w}-{w + 19}" for w in range(140, 320, 20)],
)

# average points per height bin
height_grouped = (
    df_clean.groupby("height_bin", observed=True)["avg_points"].mean().round(1)
)
weight_grouped = (
    df_clean.groupby("weight_bin", observed=True)["avg_points"].mean().round(1)
)

print("Avg points by height bin:")
print(height_grouped)
print("\nAvg points by weight bin:")
print(weight_grouped)

# calculate points per minute by height bin
ppm_grouped = (
    df_clean.groupby("height_bin", observed=True)["points_per_minute"].mean().round(3)
)

print("Avg points per minute by height bin:")
print(ppm_grouped)

# how many unique players and season rows per height bin
height_counts = (
    df_clean.groupby("height_bin", observed=True)
    .agg(season_rows=("avg_points", "count"), unique_players=("player_name", "nunique"))
    .reset_index()
)

print("\nSample size per height bin:")
print(height_counts.to_string(index=False))

# how many unique plaeyers and season rows per weight bin
weight_counts = (
    df_clean.groupby("weight_bin", observed=True)
    .agg(season_rows=("avg_points", "count"), unique_players=("player_name", "nunique"))
    .reset_index()
)

print("\nSample size per weight bin:")
print(weight_counts.to_string(index=False))

###############################################
################ Visualization ################
###############################################

fig, axes = plt.subplots(1, 3, figsize=(26, 7))
fig.suptitle(
    "Do Physical Traits Predict Scoring (across all NBA history)?", fontsize=18
)

# Avg points by height bin
height_colors = [
    "crimson" if v == height_grouped.max() else "dodgerblue"
    for v in height_grouped.values
]

axes[0].bar(
    height_grouped.index,
    height_grouped.values,
    color=height_colors,
    edgecolor="k",
    linewidth=0.8,
)

for i, (label, val) in enumerate(height_grouped.items()):
    axes[0].text(i, val + 0.1, f"{val}", ha="center", fontsize=9, fontweight="bold")

for i, (label, count) in enumerate(
    zip(height_counts["height_bin"], height_counts["season_rows"])
):
    axes[0].text(
        i,
        0.3,
        f"n =\n{count}",
        ha="center",
        fontsize=9,
        color="white",
        fontweight="bold",
    )

axes[0].set_xlabel("Height Range [in]")
axes[0].set_ylabel("Avg Points Per Game")
axes[0].set_title("Scoring by Height")
axes[0].tick_params(axis="x", rotation=45)
axes[0].set_ylim(0, height_grouped.max() + 2)
axes[0].spines["top"].set_visible(False)
axes[0].spines["right"].set_visible(False)
axes[0].grid(False)

axes[0].text(
    0.5,
    0.92,
    "The dominant height range contains less than 100 NBA players",
    transform=axes[0].transAxes,
    ha="center",
    fontsize=9,
    style="italic",
    color="gray",
)


# Avg points by weight bin
weight_colors = [
    "crimson" if v == weight_grouped.max() else "dodgerblue"
    for v in weight_grouped.values
]

axes[1].bar(
    weight_grouped.index,
    weight_grouped.values,
    color=weight_colors,
    edgecolor="k",
    linewidth=0.8,
)

for i, (label, val) in enumerate(weight_grouped.items()):
    axes[1].text(i, val + 0.1, f"{val}", ha="center", fontsize=9, fontweight="bold")

for i, (label, count) in enumerate(
    zip(weight_counts["weight_bin"], weight_counts["season_rows"])
):
    axes[1].text(
        i,
        0.3,
        f"n =\n{count}",
        ha="center",
        fontsize=9,
        color="white",
        fontweight="bold",
    )

axes[1].set_xlabel("Weight Range [lbs]")
axes[1].set_ylabel("Avg Points Per Game")
axes[1].set_title("Scoring by Weight")
axes[1].tick_params(axis="x", rotation=45)
axes[1].set_ylim(0, weight_grouped.max() + 2)
axes[1].spines["top"].set_visible(False)
axes[1].spines["right"].set_visible(False)
axes[1].grid(False)

axes[1].text(
    0.5,
    0.92,
    "Scoring is relatively consistent \nacross weight ranges with thousands of players",
    transform=axes[1].transAxes,
    ha="center",
    fontsize=9,
    style="italic",
    color="gray",
)

# Points per minute by height bin
ppm_colors = [
    "crimson" if v == ppm_grouped.max() else "dodgerblue" for v in ppm_grouped.values
]

axes[2].bar(
    ppm_grouped.index,
    ppm_grouped.values,
    color=ppm_colors,
    edgecolor="k",
    linewidth=0.8,
)

for i, (label, val) in enumerate(ppm_grouped.items()):
    axes[2].text(i, val + 0.005, f"{val}", ha="center", fontsize=9, fontweight="bold")

axes[2].set_xlabel("Height Range [in]")
axes[2].set_ylabel("Avg Points Per Minute")
axes[2].set_title("Scoring Efficiency by Height")
axes[2].tick_params(axis="x", rotation=45)
axes[2].set_ylim(0, ppm_grouped.max() + 0.1)
axes[2].spines["top"].set_visible(False)
axes[2].spines["right"].set_visible(False)
axes[2].grid(False)

axes[2].text(
    0.5,
    0.95,
    r"Players around 5.75-5.92 ft score more efficiently per minute",
    transform=axes[2].transAxes,
    ha="center",
    fontsize=9,
    style="italic",
    color="gray",
)
for i, (label, count) in enumerate(
    zip(height_counts["height_bin"], height_counts["season_rows"])
):
    axes[2].text(
        i,
        0.015,
        f"n =\n{count}",
        ha="center",
        fontsize=9,
        color="white",
        fontweight="bold",
    )

plt.tight_layout()
plt.savefig("Figures/physical_traits.png", dpi=150, bbox_inches="tight")
plt.show()
