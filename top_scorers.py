# Find the top 10 highest scoring players per season in the NBA since 2000
# What physical and effeciency traits do the greatest scorers share?

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from plot_style import set_plot_style
from matplotlib.patches import Patch

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

# Query to get top 10 highest scoring players in NBA history, along with their key stats
# What physical and effeciency traits do the greatest scorers share?
# Look into how many average points scored in season, how many points scored per minute on the floor?
# What draft round were they selected in? How tall were they? What position did they play?

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
WHERE ps.gameType = 'Regular Season' AND ps.points IS NOT NULL AND ps.numMinutes IS NOT NULL AND season_year >= '2000'
GROUP BY player_name, season_year, p.heightInches, p.bodyWeightLbs, p.draftRound, p.guard, p.forward, p.center
HAVING games_played >= 20
ORDER BY avg_points DESC
LIMIT 10
"""

# Run query and load results into a dataframe
df = pd.read_sql_query(query, conn)
conn.close()

# Results to table
print(df.to_string(index=False))

###############################################
################ Visualization ################
###############################################

# The data for draftround, guard/forward/center are not clean, so skipping
df_plot = df[['player_name', 'season_year', 'avg_points', 
              'points_per_minute', 'height_inches', 'weight_lbs']].copy()

colors = ['dodgerblue' if int(year) < 2020 else 'crimson' for year in df_plot['season_year']]


# Top 10 scorers
fig, ax = plt.subplots(figsize=(15, 7))

bars = ax.barh(df_plot['player_name'] + ' (' + df_plot['season_year'] + ')', df_plot['avg_points'],color=colors, edgecolor='k', linewidth=0.8)

for bar, val in zip(bars, df_plot['avg_points']):
    ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2, f'{val}', va='center', fontsize=12, fontweight='bold')

ax.set_xlabel('Average Points Per Game')
ax.set_title('Top 10 Highest Scoring Players Since 2000')
ax.invert_yaxis()
ax.set_xlim(0, df_plot['avg_points'].max() + 8)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(False)

legend = [Patch(color='dodgerblue', label='2000-2019'), Patch(color='crimson', label='2020-present')]

ax.legend(handles=legend, loc='lower right', bbox_to_anchor=(1, 0))

plt.tight_layout()
plt.savefig('Figures/top_scorers.png', dpi=150)
plt.show()



fig, axes = plt.subplots(1, 3, figsize=(20, 5))
fig.suptitle('Top 10 Scorers Since 2000', fontsize=18)

# Avg Points vs Height
axes[0].scatter(df_plot['height_inches'], df_plot['avg_points'],c=colors, s=200, edgecolors='k', linewidths=0.8, zorder=3)


for i, (_, row) in enumerate(df_plot.iterrows()):
    axes[0].annotate(row['player_name'].split()[-1], (row['height_inches'], row['avg_points']), textcoords="offset points",xytext=(6, 4), fontsize=7)
    
axes[0].set_xlabel('Height [in]')
axes[0].set_ylabel('Avg Points Per Game')
axes[0].set_title('Scoring vs Height')
axes[0].spines['top'].set_visible(False)
axes[0].spines['right'].set_visible(False)
axes[0].grid(False)

# Avg Points vs Weight
axes[1].scatter(df_plot['weight_lbs'],df_plot['avg_points'], c=colors, s=200, edgecolors='k', linewidths=0.8, zorder=3)

for i, (_, row) in enumerate(df_plot.iterrows()):
    axes[1].annotate(row['player_name'].split()[-1], (row['weight_lbs'], row['avg_points']), textcoords="offset points", xytext=(6, 4), fontsize=7)
    
axes[1].set_xlabel('Weight [lbs]')
axes[1].set_ylabel('Avg Points Per Game')
axes[1].set_title('Scoring vs Weight')
axes[1].spines['top'].set_visible(False)
axes[1].spines['right'].set_visible(False)
axes[1].grid(False)

# Avg Points vs Points Per Minute-
axes[2].scatter(df_plot['points_per_minute'], df_plot['avg_points'],c=colors, s=200, edgecolors='k', linewidths=0.8, zorder=3)

for i, (_, row) in enumerate(df_plot.iterrows()):
    axes[2].annotate(row['player_name'].split()[-1] + ' (' + row['season_year'] + ')', (row['points_per_minute'], row['avg_points']), textcoords="offset points", xytext=(6, 4), fontsize=7)
    
axes[2].set_xlabel('Points Per Minute')
axes[2].set_ylabel('Avg Points Per Game')
axes[2].set_title('Volume Scoring vs Efficiency')
axes[2].spines['top'].set_visible(False)
axes[2].spines['right'].set_visible(False)
axes[2].grid(False)

legend = [Patch(color='dodgerblue', label='2000-2019'), Patch(color='crimson', label='2020-present')]

fig.legend(handles=legend, loc='lower center', ncol=2, fontsize=12, bbox_to_anchor=(0.5, 0))

plt.tight_layout(rect=[0, 0.06, 1, 1])
plt.savefig('Figures/top_scorers_physical.png', dpi=150, bbox_inches='tight')
plt.show()
