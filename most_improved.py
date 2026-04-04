# For every player, how much did their scoring average change compared to the previous season?
# Who had the biggest single-season jump?

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from plot_style import set_plot_style
from matplotlib.patches import Patch

set_plot_style()

###############################################
######### Connection to SQL Database ##########
###############################################

conn = sqlite3.connect("nba.db")

###############################################
################## SQL Query ##################
###############################################

query = """
WITH seasonal_averages AS (
    SELECT
        ps.firstName || ' ' || ps.lastName AS player_name,
        SUBSTR(ps.gameDateTimeEst, 1, 4) AS season_year,
        COUNT(ps.gameId) AS games_played,
        ROUND(AVG(ps.points), 1) AS avg_points
    FROM PlayerStatistics ps
    WHERE ps.gameType = 'Regular Season' AND ps.points IS NOT NULL
    GROUP BY player_name, season_year
    HAVING games_played >= 20
),
with_previous AS (
    SELECT 
        player_name,
        season_year,
        avg_points,
        LAG(avg_points) OVER (PARTITION BY player_name ORDER BY season_year) AS prev_avg_points,
        LEAD(avg_points) OVER (PARTITION BY player_name ORDER BY season_year) AS next_avg_points
    FROM seasonal_averages
),
improvement AS (
    SELECT 
        player_name,
        season_year,
        avg_points,
        prev_avg_points,
        next_avg_points,
        ROUND(avg_points - prev_avg_points, 1) AS points_improvement,
        ROUND((avg_points - prev_avg_points) / prev_avg_points * 100, 1) AS pct_improvement,
        CASE
            WHEN next_avg_points >= avg_points * 0.9 THEN 'Sustained'
            WHEN next_avg_points IS NULL THEN 'Unknown'
            ELSE 'One year'
        END AS improvement_type
    FROM with_previous
    WHERE prev_avg_points IS NOT NULL
        AND prev_avg_points >= 5
)
SELECT * FROM improvement
WHERE season_year >= '2000'
ORDER BY points_improvement DESC
LIMIT 20
"""

df = pd.read_sql_query(query, conn)
conn.close()

print(df.to_string(index=False))

###############################################
################ Visualization ################
###############################################

fig, axes = plt.subplots(1, 2, figsize=(22, 8))
fig.suptitle("NBA Most Improved Scorers (2000-Present)", fontsize=18)

# Biggest scoring jumps
improvement_colors = [
    "crimson" if val >= 12 else "dodgerblue" for val in df["points_improvement"]
]

axes[0].barh(
    df["player_name"] + " (" + df["season_year"] + ")",
    df["points_improvement"],
    color=improvement_colors,
    edgecolor="k",
    linewidth=0.8,
)

for bar, val, pct in zip(
    axes[0].patches, df["points_improvement"], df["pct_improvement"]
):
    axes[0].text(
        val + 0.1,
        bar.get_y() + bar.get_height() / 2,
        f"+{val} ({pct}%)",
        va="center",
        fontsize=10,
        fontweight="bold",
    )

axes[0].set_xlabel("Points Per Game Improvement")
axes[0].set_title("Biggest Single Season Scoring Jumps")
axes[0].invert_yaxis()
axes[0].set_xlim(0, df["points_improvement"].max() + 8)
axes[0].spines["top"].set_visible(False)
axes[0].spines["right"].set_visible(False)
axes[0].grid(False)

legend = [
    Patch(color="crimson", label="12+ PPG jump"),
    Patch(color="dodgerblue", label="10-12 PPG jump"),
]
axes[0].legend(handles=legend, fontsize=10)

# Before vs After comparison
y = range(len(df))
height = 0.35

axes[1].barh(
    [i + height / 2 for i in y],
    df["avg_points"],
    height=height,
    color="crimson",
    edgecolor="k",
    linewidth=0.8,
    label="Season of improvement",
)
axes[1].barh(
    [i - height / 2 for i in y],
    df["prev_avg_points"],
    height=height,
    color="dodgerblue",
    edgecolor="k",
    linewidth=0.8,
    label="Previous season",
)

for i, (val, pct) in enumerate(zip(df["avg_points"], df["pct_improvement"])):
    axes[1].text(
        val + 0.3,
        i + height / 2,
        f"+{pct}%",
        va="center",
        fontsize=8,
        color="crimson",
        fontweight="bold",
    )

axes[1].set_yticks(list(y))
axes[1].set_yticklabels(
    [
        name.split()[-1] + " (" + year + ")"
        for name, year in zip(df["player_name"], df["season_year"])
    ],
    fontsize=9,
)
axes[1].invert_yaxis()
axes[1].set_xlabel("Avg Points Per Game")
axes[1].set_title("Before vs After: Scoring Comparison")
axes[1].set_xlim(0, df["avg_points"].max() + 8)
axes[1].legend(fontsize=10, loc="lower right")
axes[1].spines["top"].set_visible(False)
axes[1].spines["right"].set_visible(False)
axes[1].grid(False)

plt.tight_layout()
plt.savefig("Figures/most_improved.png", dpi=150)
plt.show()
