# For the 2026 regular season, which teams score the most, allow the least, and have the best point differential on average per game?
# Does that predict who wins?

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

# compute offensive efficiency: how many points does this team score per game?
# compute defensive efficiency: how many points does this team allow per game?
# compute point differential: how many points do they outscore opponents by on average?
query = """
WITH team_efficiency AS (
    SELECT
        ts.teamCity || ' ' || ts.teamName AS team_name,
        SUBSTR(ts.gameDateTimeEst, 1, 4) AS season_year,
        COUNT(ts.gameID) AS games_played,
        
        ROUND(AVG(ts.teamScore), 1) AS avg_points_scored,
        ROUND(AVG(ts.opponentScore), 1) AS avg_points_allowed,
        ROUND(AVG(ts.teamScore - ts.opponentScore), 1) AS avg_point_diff,
        ROUND(SUM(ts.win) * 100.0 / COUNT(ts.gameID), 1) AS win_rate,
        ROUND(AVG(ts.assists), 1) AS avg_assists,
        ROUND(AVG(ts.threePointersMade), 1) AS avg_threes
        
        FROM TeamStatistics ts
        JOIN Games g ON ts.gameID = g.gameID WHERE g.gameType = 'Regular Season' AND SUBSTR(ts.gameDateTimeEst, 1, 4) = '2026'
        GROUP BY team_name, season_year
        HAVING games_played >= 40
),
ranked AS (
    SELECT *,
        RANK() OVER (ORDER BY avg_point_diff DESC) AS efficiency_rank
    FROM team_efficiency
)
SELECT * FROM ranked
ORDER BY efficiency_rank
"""

df = pd.read_sql_query(query, conn)
conn.close()

print(df.to_string(index=False))

###############################################
################ Visualization ################
###############################################

fig, axes = plt.subplots(1, 3, figsize=(28, 8))
fig.suptitle("NBA Team Efficiency: 2026 Regular Season", fontsize=18)

# offense vs defense by win rate
scatter_colors = ["dodgerblue" if d > 0 else "crimson" for d in df["avg_point_diff"]]

axes[0].scatter(
    df["avg_points_scored"],
    df["avg_points_allowed"],
    c=scatter_colors,
    s=df["win_rate"] * 5,
    edgecolors="k",
    linewidths=0.8,
    zorder=3,
    alpha=0.8,
)

for i, row in df.iterrows():
    axes[0].annotate(
        row["team_name"].split()[-1],
        (row["avg_points_scored"], row["avg_points_allowed"]),
        textcoords="offset points",
        xytext=(6, 4),
        fontsize=8,
    )

# break even diagonal
min_val = min(df["avg_points_scored"].min(), df["avg_points_allowed"].min()) - 1
max_val = max(df["avg_points_scored"].max(), df["avg_points_allowed"].max()) + 1
axes[0].plot(
    [min_val, max_val],
    [min_val, max_val],
    color="gray",
    linestyle="--",
    linewidth=1,
    alpha=0.6,
)

axes[0].text(
    df["avg_points_scored"].max() - 0.5,
    df["avg_points_allowed"].min() + 0.3,
    "Elite",
    fontsize=9,
    color="dodgerblue",
    ha="right",
    fontweight="bold",
)
axes[0].text(
    df["avg_points_scored"].min() + 0.3,
    df["avg_points_allowed"].max() - 0.3,
    "Struggling",
    fontsize=9,
    color="crimson",
    fontweight="bold",
)

axes[0].set_xlabel("Avg Points Scored Per Game")
axes[0].set_ylabel("Avg Points Allowed Per Game")
axes[0].set_title("Offense vs Defense\n(dot size = win rate)")
axes[0].spines["top"].set_visible(False)
axes[0].spines["right"].set_visible(False)
axes[0].grid(False)

legend = [
    Patch(color="dodgerblue", label="Positive differential"),
    Patch(color="crimson", label="Negative differential"),
]
axes[0].legend(handles=legend, fontsize=9)

# Point differential bar chart
df_sorted = df.sort_values("avg_point_diff", ascending=True)
bar_colors = ["dodgerblue" if d > 0 else "crimson" for d in df_sorted["avg_point_diff"]]

axes[1].barh(
    df_sorted["team_name"].str.split().str[-1],
    df_sorted["avg_point_diff"],
    color=bar_colors,
    edgecolor="k",
    linewidth=0.8,
)

for bar, diff, wr in zip(
    axes[1].patches, df_sorted["avg_point_diff"], df_sorted["win_rate"]
):
    label = f"+{diff} ({wr}% wins)" if diff > 0 else f"{diff} ({wr}% wins)"
    x_pos = diff + 0.2 if diff >= 0 else diff - 0.2
    ha = "left" if diff >= 0 else "right"
    axes[1].text(
        x_pos,
        bar.get_y() + bar.get_height() / 2,
        label,
        va="center",
        fontsize=8,
        fontweight="bold",
        ha=ha,
    )

axes[1].axvline(x=0, color="black", linewidth=0.8)
axes[1].set_xlabel("Avg Point Differential Per Game")
axes[1].set_title("Point Differential vs Win Rate\n(best to worst)")
axes[1].spines["top"].set_visible(False)
axes[1].spines["right"].set_visible(False)
axes[1].grid(False)
axes[1].set_xlim(
    df_sorted['avg_point_diff'].min() - 6, 
    df_sorted['avg_point_diff'].max() + 8 
)

# Assists vs point differential scatter - does ball movement correlate with winning?
axes[2].scatter(
    df["avg_assists"],
    df["avg_point_diff"],
    c=scatter_colors,
    s=200,
    edgecolors="k",
    linewidths=0.8,
    zorder=3,
)

for i, row in df.iterrows():
    axes[2].annotate(
        row["team_name"].split()[-1],
        (row["avg_assists"], row["avg_point_diff"]),
        textcoords="offset points",
        xytext=(6, 4),
        fontsize=8,
    )

axes[2].axhline(y=0, color="gray", linestyle="--", linewidth=1, alpha=0.6)

axes[2].set_xlabel("Avg Assists Per Game")
axes[2].set_ylabel("Avg Point Differential")
axes[2].set_title("Ball Movement vs Winning\n(do unselfish teams win more?)")
axes[2].spines["top"].set_visible(False)
axes[2].spines["right"].set_visible(False)
axes[2].grid(False)
axes[2].set_xlim(
    df['avg_assists'].min() - 0.5,
    df['avg_assists'].quantile(0.85) + 1
)

warriors = df[df['team_name'].str.contains('Warriors')].iloc[0]
if warriors['avg_assists'] > axes[2].get_xlim()[1]:
    axes[2].annotate(
        f"Warriors ({warriors['avg_assists']} AST) →",
        xy=(axes[2].get_xlim()[1], warriors['avg_point_diff']),
        fontsize=7, color='crimson', ha='right'
    )

legend2 = [
    Patch(color="dodgerblue", label="Positive differential"),
    Patch(color="crimson", label="Negative differential"),
]
axes[2].legend(handles=legend2, fontsize=9)

plt.tight_layout()
plt.savefig("Figures/team_efficiency.png", dpi=150, bbox_inches="tight")
plt.show()
