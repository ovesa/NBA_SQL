# Who is the go-to scorer on each team each season, and which players have been their team's top scorer most consistently?

import sqlite3
import pandas as pd
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
from plot_style import set_plot_style
set_plot_style()


###############################################
######### Connection to SQL Database ##########
###############################################

conn = sqlite3.connect("nba.db")

###############################################
################## SQL Query ##################
###############################################

# In each season since 2000, who scored the most on the team?
# Across all team, who were the highest scoring players?

query = """
WITH seasonal_averages AS (
    SELECT
        ps.firstName || ' ' || ps.lastName AS player_name,
        ps.playerteamCity || ' ' || ps.playerteamName AS team_name,
        SUBSTR(ps.gameDateTimeEst, 1, 4) AS season_year,
        COUNT(ps.gameId) AS games_played,
        ROUND(AVG(ps.points), 1) AS avg_points
    FROM PlayerStatistics ps
    WHERE ps.gameType = 'Regular Season' AND ps.points IS NOT NULL
    GROUP BY player_name, team_name, season_year
    HAVING games_played >= 20
),
ranked AS (
    SELECT *,
        RANK() OVER (
            PARTITION BY team_name, season_year
            ORDER BY avg_points DESC
        ) AS scoring_rank
    FROM seasonal_averages
)
SELECT * FROM ranked
WHERE scoring_rank = 1 AND season_year >= '2000'
ORDER BY avg_points DESC
LIMIT 20
"""

# Since 2000, which players have consistently been their team's primary scorer across all seasons?

query2 = """
WITH seasonal_averages AS (
    SELECT
        ps.firstName || ' ' || ps.lastName AS player_name,
        ps.playerteamCity || ' ' || ps.playerteamName AS team_name,
        SUBSTR(ps.gameDateTimeEst, 1, 4) AS season_year,
        COUNT(ps.gameId) AS games_played,
        ROUND(AVG(ps.points), 1) AS avg_points
    FROM PlayerStatistics ps
    WHERE ps.gameType = 'Regular Season'
        AND ps.points IS NOT NULL
    GROUP BY player_name, team_name, season_year
    HAVING games_played >= 20
),
ranked AS (
    SELECT *,
        RANK() OVER (
            PARTITION BY team_name, season_year
            ORDER BY avg_points DESC
        ) AS scoring_rank
    FROM seasonal_averages
)
SELECT player_name, COUNT(*) AS times_led_team
FROM ranked
WHERE scoring_rank = 1 AND season_year >= '2000'
GROUP BY player_name
HAVING times_led_team >= 7
ORDER BY times_led_team DESC
"""

df = pd.read_sql_query(query, conn)
df2 = pd.read_sql_query(query2, conn)
conn.close()

print(df.to_string(index=False))
print(df2.to_string(index=False))

###############################################
################ Visualization ################
###############################################

fig, axes = plt.subplots(1, 2, figsize=(18, 7))
fig.suptitle('NBA Team Leading Scorers (2000-Present)', fontsize=18)

# Top 20 leading scorers 
bar_colors = ['crimson' if year >= '2020' else 'dodgerblue' for year in df['season_year']]

axes[0].barh(
    df['player_name'] + ' (' + df['season_year'] + ')',
    df['avg_points'],
    color=bar_colors,
    edgecolor='k', linewidth=0.8
)

for bar, val in zip(axes[0].patches, df['avg_points']):
    axes[0].text(val + 0.2, bar.get_y() + bar.get_height() / 2, f'{val}', va='center', fontsize=12, fontweight='bold')

axes[0].set_xlabel('Avg Points Per Game')
axes[0].set_title('Top 20 Team Leading Scorers')
axes[0].invert_yaxis()
axes[0].set_xlim(0, df['avg_points'].max() + 8)
axes[0].spines['top'].set_visible(False)
axes[0].spines['right'].set_visible(False)
axes[0].grid(False)

legend = [
    Patch(color='dodgerblue', label='2000-2019'),
    Patch(color='crimson', label='2020-present')
]

axes[0].legend(handles=legend, fontsize=10, ncol=2, loc='upper left')


axes[1].barh( df2['player_name'], df2['times_led_team'], color='dodgerblue', edgecolor='k', linewidth=0.8)

for bar, val in zip(axes[1].patches, df2['times_led_team']):
    axes[1].text(val + 0.05, bar.get_y() + bar.get_height() / 2, str(val), va='center', fontsize=12, fontweight='bold')
    
axes[1].tick_params(axis='y', labelsize=12)
axes[1].set_xlabel('Number of Seasons as Team\'s Top Scorer')
axes[1].set_title(r'Most Seasons Leading Team ($\geq$7) in Scoring')
axes[1].invert_yaxis()
axes[1].set_xlim(0, df2['times_led_team'].max() + 2)
axes[1].spines['top'].set_visible(False)
axes[1].spines['right'].set_visible(False)
axes[1].grid(False)

plt.tight_layout()
plt.savefig('Figures/player_rankings.png', dpi=150)
plt.show()