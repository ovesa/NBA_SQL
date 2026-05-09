# What are the biggest blowouts in NBA history?
# Who was on each side of them?

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
SELECT
    g.gameId,
    SUBSTR(g.gameDateTimeEst, 1, 4) AS season_year,
    SUBSTR(g.gameDateTimeEst, 1, 10) AS game_date,
    g.hometeamCity || ' ' || g.hometeamName AS home_team,
    g.awayteamCity || ' ' || g.awayteamName AS away_team,
    g.homeScore,
    g.awayScore,

    ABS(g.homeScore - g.awayScore) AS margin,

    CASE
        WHEN g.homeScore > g.awayScore
            THEN g.hometeamCity || ' ' || g.hometeamName
        ELSE g.awayteamCity || ' ' || g.awayteamName
    END AS winning_team,

    CASE
        WHEN g.homeScore > g.awayScore
            THEN g.awayteamCity || ' ' || g.awayteamName
        ELSE g.hometeamCity || ' ' || g.hometeamName
    END AS losing_team,

    CASE WHEN g.homeScore > g.awayScore THEN g.homeScore ELSE g.awayScore END AS winning_score,
    CASE WHEN g.homeScore > g.awayScore THEN g.awayScore ELSE g.homeScore END AS losing_score,

    CASE
        WHEN SUBSTR(g.gameDateTimeEst, 1, 4) < '1960' THEN '1950s'
        WHEN SUBSTR(g.gameDateTimeEst, 1, 4) < '1970' THEN '1960s'
        WHEN SUBSTR(g.gameDateTimeEst, 1, 4) < '1980' THEN '1970s'
        WHEN SUBSTR(g.gameDateTimeEst, 1, 4) < '1990' THEN '1980s'
        WHEN SUBSTR(g.gameDateTimeEst, 1, 4) < '2000' THEN '1990s'
        WHEN SUBSTR(g.gameDateTimeEst, 1, 4) < '2010' THEN '2000s'
        WHEN SUBSTR(g.gameDateTimeEst, 1, 4) < '2020' THEN '2010s'
        ELSE '2020s'
    END AS decade,

    g.gameType,
    g.attendance

FROM Games g
WHERE g.gameType = 'Regular Season'
    AND g.homeScore IS NOT NULL
    AND g.awayScore IS NOT NULL
    AND g.homeScore > 0
    AND g.awayScore > 0
    AND SUBSTR(g.gameDateTimeEst, 1, 4) >= '1970'
ORDER BY margin DESC
LIMIT 20
"""

df = pd.read_sql_query(query, conn)
conn.close()

print(df.to_string(index=False))

###############################################
################ Visualization ################
###############################################
###############################################
################ Visualization ################
###############################################

# map each decade to a color
decade_colors = {
    "1970s": "dodgerblue",
    "1980s": "navy",
    "1990s": "goldenrod",
    "2000s": "orange",
    "2010s": "pink",
    "2020s": "darkred",
}

bar_colors = [decade_colors.get(d, "gray") for d in df["decade"]]

fig, axes = plt.subplots(1, 2, figsize=(22, 8))
fig.suptitle("Biggest Blowouts in NBA History (1970-Present)", fontsize=18)

# Margin of victory bar
axes[0].barh(
    df["winning_team"].str.split().str[-1]
    + " def. "
    + df["losing_team"].str.split().str[-1]
    + " ("
    + df["game_date"].str[:4]
    + ")",
    df["margin"],
    color=bar_colors,
    edgecolor="k",
    linewidth=0.8,
)

for bar, val in zip(axes[0].patches, df["margin"]):
    axes[0].text(
        val + 0.3,
        bar.get_y() + bar.get_height() / 2,
        f"+{val}",
        va="center",
        fontsize=10,
        fontweight="bold",
    )

axes[0].set_xlabel("Margin of Victory (points)")
axes[0].set_title("Top 20 Biggest Blowouts")
axes[0].invert_yaxis()
axes[0].set_xlim(0, df["margin"].max() + 10)
axes[0].spines["top"].set_visible(False)
axes[0].spines["right"].set_visible(False)
axes[0].grid(False)

# only show decades that actually appear in the data
legend = [
    Patch(color=color, label=decade)
    for decade, color in decade_colors.items()
    if decade in df["decade"].values
]
axes[0].legend(handles=legend, fontsize=9, ncol=5, loc="lower right")

# Winning vs losing score comparison
y = range(len(df))
height = 0.35

axes[1].barh(
    [i + height / 2 for i in y],
    df["winning_score"],
    height=height,
    color="dodgerblue",
    edgecolor="k",
    linewidth=0.8,
    label="Winning score",
)
axes[1].barh(
    [i - height / 2 for i in y],
    df["losing_score"],
    height=height,
    color="crimson",
    edgecolor="k",
    linewidth=0.8,
    label="Losing score",
)

for i, row in df.iterrows():
    axes[1].text(
        row["winning_score"] + 0.5,
        i,
        f"+{int(row['margin'])} pts",
        va="center",
        fontsize=9,
        color="black",
        fontweight="bold",
    )

axes[1].set_yticks(list(y))
axes[1].set_yticklabels(
    [
        win.split()[-1] + " vs " + lose.split()[-1]
        for win, lose in zip(df["winning_team"], df["losing_team"])
    ],
    fontsize=9,
)
axes[1].invert_yaxis()
axes[1].set_xlabel("Points Scored")
axes[1].set_title("Winning vs Losing Score")
axes[1].set_xlim(0, df["winning_score"].max() + 15)
axes[1].legend(fontsize=10, loc="lower right",ncol=2)
axes[1].spines["top"].set_visible(False)
axes[1].spines["right"].set_visible(False)
axes[1].grid(False)

plt.tight_layout()
plt.savefig("Figures/blowouts.png", dpi=150, bbox_inches="tight")
plt.show()
