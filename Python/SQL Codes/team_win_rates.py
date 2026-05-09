# Analyze NBA team wins, losses, games played, and win rate by season to identify the most dominant teams in recent history

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from plot_style import set_plot_style

# Import custom plot styles
set_plot_style()

###############################################
######### Connection to SQL Database ##########
###############################################

conn = sqlite3.connect("nba.db")

###############################################
################## SQL Query ##################
###############################################

# For each team in each season, calculate their win rate
# Only look at regular season games from 2000 onwards
# Compute win rate as a percentage of wins out of total games played
# Filter for teams that played at least 20 games in a season to ensure meaningful win rates

query = """
SELECT
    ts.teamName AS team_name,
    SUBSTR(ts.gameDateTimeEst, 1, 4) AS season_year,
    COUNT(ts.gameId) AS games_played,
    COUNT(ts.gameId) - SUM(ts.win) AS losses,
    SUM(ts.win) AS wins,
    ROUND(SUM(ts.win) * 100.0 / COUNT(ts.gameId), 1) AS win_rate
FROM TeamStatistics ts
JOIN Games g ON ts.gameId = g.gameId AND g.gameType = 'Regular Season' AND SUBSTR(ts.gameDateTimeEst, 1, 4) >= '2000'
GROUP BY team_name, season_year
HAVING games_played >= 20
ORDER BY season_year, win_rate DESC
"""

# Run query and load results into a dataframe
df = pd.read_sql_query(query, conn)
conn.close()

print(df.head(20).to_string(index=False))

df["wins"] = df["wins"].astype(int)
df["losses"] = df["losses"].astype(int)

###############################################
################ Visualization ################
###############################################

# Top 10 best single seasons by win rate
fig, axes = plt.subplots(1, 2, figsize=(20, 7))
fig.suptitle("NBA Team Win Rates Since 2000", fontsize=18)

# Top 10 best seasons
top_seasons = df.nlargest(10, "win_rate").copy()
labels = top_seasons["team_name"] + " (" + top_seasons["season_year"] + ")"

axes[0].barh(
    labels,
    top_seasons["wins"],
    color="dodgerblue",
    edgecolor="k",
    linewidth=0.8,
    label="Wins",
)

axes[0].barh(
    labels,
    top_seasons["losses"],
    left=top_seasons["wins"],
    color="crimson",
    edgecolor="k",
    linewidth=0.8,
    label="Losses",
)

for i, (wins, losses, rate) in enumerate(
    zip(top_seasons["wins"], top_seasons["losses"], top_seasons["win_rate"])
):
    total = wins + losses
    axes[0].text(
        total + 0.5,
        i,
        f"{rate}%  ({wins}W - {losses}L)",
        va="center",
        fontsize=9,
        fontweight="bold",
    )

axes[0].set_xlabel("Games")
axes[0].set_title("Top 10 Best Single Seasons\n(wins vs losses)")
axes[0].invert_yaxis()
axes[0].set_xlim(0, 115)
axes[0].legend(fontsize=12)
axes[0].spines["top"].set_visible(False)
axes[0].spines["right"].set_visible(False)
axes[0].grid(False)

# Win rate trend over time
teams_to_plot = ["Lakers", "Celtics", "Bulls", "Warriors", "Spurs"]
colors = ["dodgerblue", "goldenrod", "crimson", "k", "purple"]

for team, color in zip(teams_to_plot, colors):
    team_df = df[df["team_name"].str.contains(team)].copy()
    team_df = team_df.sort_values("season_year")

    axes[1].plot(
        team_df["season_year"],
        team_df["win_rate"],
        marker="o",
        color=color,
        markersize=5,
        linewidth=2,
        label=team,
    )

axes[1].set_xlabel("Season Year")
axes[1].set_ylabel(r"Win Rate [$\%$]")
axes[1].set_title("Win Rate Over Time")
axes[1].legend(loc="center left", bbox_to_anchor=(1, 0.5))
axes[1].spines["top"].set_visible(False)
axes[1].spines["right"].set_visible(False)
axes[1].grid(False)
axes[1].set_ylim(0, 100)

years = sorted(df["season_year"].unique())
axes[1].set_xticks([y for y in years if int(y) % 5 == 0])
axes[1].tick_params(axis="x", rotation=10)

plt.tight_layout()
plt.savefig("Figures/team_win_rates.png", dpi=150)
plt.show()
