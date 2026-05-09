###################################################################################
# NBA Historical Analytics Dashboard
# Run: python dashboard.py
# Then open: http://localhost:8050
# Created show results on a dashboard with interactive charts using Plotly and Dash
###################################################################################

import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import os

###################################################################################

# color matching
color_blue = "dodgerblue"
color_red = "crimson"
color_gold = "goldenrod"
color_gray = "gray"
color_green = "forestgreen"
color_purple = "purple"

###################################################################################
############################# Set up Dash & Load Data #############################
###################################################################################

app = Dash(__name__, title="NBA Analytics Dashboard")

# Load data
db_path = os.path.join(os.path.dirname(__file__), "nba.db")

def get_conn():
    return sqlite3.connect(db_path)

# grabbed queries from other files and wrapped in functions to load into dataframes on app start
def load_top_scorers():
    q = """
    SELECT
        ps.firstName || ' ' || ps.lastName AS player_name,
        SUBSTR(ps.gameDateTimeEst, 1, 4) AS season_year,
        COUNT(ps.gameId) AS games_played,
        ROUND(AVG(ps.points), 1) AS avg_points,
        ROUND(AVG(ps.points) / NULLIF(AVG(ps.numMinutes), 0), 2) AS points_per_minute,
        p.heightInches AS height_inches,
        p.bodyWeightLbs AS weight_lbs
    FROM PlayerStatistics ps
    JOIN Players p ON ps.personId = p.personId
    WHERE ps.gameType = 'Regular Season'
      AND ps.points IS NOT NULL
      AND ps.numMinutes IS NOT NULL
      AND SUBSTR(ps.gameDateTimeEst, 1, 4) >= '2000'
    GROUP BY player_name, season_year, p.heightInches, p.bodyWeightLbs
    HAVING games_played >= 20
    ORDER BY avg_points DESC
    LIMIT 10
    """
    with get_conn() as conn:
        return pd.read_sql_query(q, conn)


def load_all_top_scorers():
    q = """
    SELECT
        ps.firstName || ' ' || ps.lastName AS player_name,
        SUBSTR(ps.gameDateTimeEst, 1, 4) AS season_year,
        COUNT(ps.gameId) AS games_played,
        ROUND(AVG(ps.points), 1) AS avg_points,
        ROUND(AVG(ps.points) / NULLIF(AVG(ps.numMinutes), 0), 2) AS points_per_minute,
        p.heightInches AS height_inches,
        p.bodyWeightLbs AS weight_lbs
    FROM PlayerStatistics ps
    JOIN Players p ON ps.personId = p.personId
    WHERE ps.gameType = 'Regular Season'
      AND ps.points IS NOT NULL
      AND ps.numMinutes IS NOT NULL
    GROUP BY player_name, season_year, p.heightInches, p.bodyWeightLbs
    HAVING games_played >= 20
    ORDER BY avg_points DESC
    """
    with get_conn() as conn:
        return pd.read_sql_query(q, conn)


def load_team_win_rates():
    q = """
    SELECT
        ts.teamName AS team_name,
        SUBSTR(ts.gameDateTimeEst, 1, 4) AS season_year,
        COUNT(ts.gameId) AS games_played,
        COUNT(ts.gameId) - SUM(ts.win) AS losses,
        SUM(ts.win) AS wins,
        ROUND(SUM(ts.win) * 100.0 / COUNT(ts.gameId), 1) AS win_rate
    FROM TeamStatistics ts
    JOIN Games g ON ts.gameId = g.gameId
      AND g.gameType = 'Regular Season'
      AND SUBSTR(ts.gameDateTimeEst, 1, 4) >= '2000'
    GROUP BY team_name, season_year
    HAVING games_played >= 20
    ORDER BY season_year, win_rate DESC
    """
    with get_conn() as conn:
        return pd.read_sql_query(q, conn)


def load_player_rankings():
    q1 = """
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
            RANK() OVER (PARTITION BY team_name, season_year ORDER BY avg_points DESC) AS scoring_rank
        FROM seasonal_averages
    )
    SELECT * FROM ranked
    WHERE scoring_rank = 1 AND season_year >= '2000'
    ORDER BY avg_points DESC
    LIMIT 20
    """
    q2 = """
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
            RANK() OVER (PARTITION BY team_name, season_year ORDER BY avg_points DESC) AS scoring_rank
        FROM seasonal_averages
    )
    SELECT player_name, COUNT(*) AS times_led_team
    FROM ranked
    WHERE scoring_rank = 1 AND season_year >= '2000'
    GROUP BY player_name
    HAVING times_led_team >= 7
    ORDER BY times_led_team DESC
    """
    with get_conn() as conn:
        return pd.read_sql_query(q1, conn), pd.read_sql_query(q2, conn)


def load_most_improved():
    q = """
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
            player_name, season_year, avg_points,
            LAG(avg_points) OVER (PARTITION BY player_name ORDER BY season_year) AS prev_avg_points,
            LEAD(avg_points) OVER (PARTITION BY player_name ORDER BY season_year) AS next_avg_points
        FROM seasonal_averages
    ),
    improvement AS (
        SELECT
            player_name, season_year, avg_points, prev_avg_points, next_avg_points,
            ROUND(avg_points - prev_avg_points, 1) AS points_improvement,
            ROUND((avg_points - prev_avg_points) / prev_avg_points * 100, 1) AS pct_improvement,
            CASE
                WHEN next_avg_points >= avg_points * 0.9 THEN 'Sustained'
                WHEN next_avg_points IS NULL THEN 'Unknown'
                ELSE 'One year'
            END AS improvement_type
        FROM with_previous
        WHERE prev_avg_points IS NOT NULL AND prev_avg_points >= 5
    )
    SELECT * FROM improvement
    WHERE season_year >= '2000'
    ORDER BY points_improvement DESC
    LIMIT 20
    """
    with get_conn() as conn:
        return pd.read_sql_query(q, conn)


def load_team_efficiency():
    q = """
    WITH team_efficiency AS (
        SELECT
            ts.teamCity || ' ' || ts.teamName AS team_name,
            SUBSTR(ts.gameDateTimeEst, 1, 4) AS season_year,
            COUNT(ts.gameID) AS games_played,
            ROUND(AVG(ts.teamScore), 1) AS avg_points_scored,
            ROUND(AVG(ts.opponentScore), 1) AS avg_points_allowed,
            ROUND(AVG(ts.teamScore - ts.opponentScore), 1) AS avg_point_diff,
            ROUND(SUM(ts.win) * 100.0 / COUNT(ts.gameID), 1) AS win_rate,
            ROUND(AVG(ts.assists), 1) AS avg_assists
        FROM TeamStatistics ts
        JOIN Games g ON ts.gameID = g.gameID
        WHERE g.gameType = 'Regular Season'
          AND SUBSTR(ts.gameDateTimeEst, 1, 4) = '2026'
        GROUP BY team_name, season_year
        HAVING games_played >= 40
    ),
    ranked AS (
        SELECT *, RANK() OVER (ORDER BY avg_point_diff DESC) AS efficiency_rank
        FROM team_efficiency
    )
    SELECT * FROM ranked ORDER BY efficiency_rank
    """
    with get_conn() as conn:
        return pd.read_sql_query(q, conn)


def load_blowouts():
    q = """
    SELECT
        g.gameId,
        SUBSTR(g.gameDateTimeEst, 1, 4) AS season_year,
        SUBSTR(g.gameDateTimeEst, 1, 10) AS game_date,
        g.hometeamCity || ' ' || g.hometeamName AS home_team,
        g.awayteamCity || ' ' || g.awayteamName AS away_team,
        g.homeScore, g.awayScore,
        ABS(g.homeScore - g.awayScore) AS margin,
        CASE WHEN g.homeScore > g.awayScore THEN g.hometeamCity || ' ' || g.hometeamName
             ELSE g.awayteamCity || ' ' || g.awayteamName END AS winning_team,
        CASE WHEN g.homeScore > g.awayScore THEN g.awayteamCity || ' ' || g.awayteamName
             ELSE g.hometeamCity || ' ' || g.hometeamName END AS losing_team,
        CASE WHEN g.homeScore > g.awayScore THEN g.homeScore ELSE g.awayScore END AS winning_score,
        CASE WHEN g.homeScore > g.awayScore THEN g.awayScore ELSE g.homeScore END AS losing_score,
        CASE
            WHEN SUBSTR(g.gameDateTimeEst,1,4) < '1980' THEN '1970s'
            WHEN SUBSTR(g.gameDateTimeEst,1,4) < '1990' THEN '1980s'
            WHEN SUBSTR(g.gameDateTimeEst,1,4) < '2000' THEN '1990s'
            WHEN SUBSTR(g.gameDateTimeEst,1,4) < '2010' THEN '2000s'
            WHEN SUBSTR(g.gameDateTimeEst,1,4) < '2020' THEN '2010s'
            ELSE '2020s'
        END AS decade
    FROM Games g
    WHERE g.gameType = 'Regular Season'
      AND g.homeScore IS NOT NULL AND g.awayScore IS NOT NULL
      AND g.homeScore > 0 AND g.awayScore > 0
      AND SUBSTR(g.gameDateTimeEst,1,4) >= '1970'
    ORDER BY margin DESC
    LIMIT 20
    """
    with get_conn() as conn:
        return pd.read_sql_query(q, conn)


# Pre-load all dataframes
df_top = load_top_scorers()
df_all = load_all_top_scorers()
df_win = load_team_win_rates()
df_lead, df_consist = load_player_rankings()
df_imp = load_most_improved()
df_eff = load_team_efficiency()
df_blow = load_blowouts()

# Physical trait bins from df_all
df_clean = df_all.dropna(subset=["height_inches", "weight_lbs"]).copy()
df_clean["height_bin"] = pd.cut(df_clean["height_inches"], bins=range(63, 95, 3),
    labels=[f"{h}–{h+2}" for h in range(63, 92, 3)])
df_clean["weight_bin"] = pd.cut(df_clean["weight_lbs"], bins=range(140, 340, 20),
    labels=[f"{w}–{w+19}" for w in range(140, 320, 20)])

height_grouped = df_clean.groupby("height_bin", observed=True)["avg_points"].mean().round(1)
height_counts = df_clean.groupby("height_bin", observed=True)["avg_points"].count()
weight_grouped = df_clean.groupby("weight_bin", observed=True)["avg_points"].mean().round(1)
weight_counts = df_clean.groupby("weight_bin", observed=True)["avg_points"].count()
ppm_grouped = df_clean.groupby("height_bin", observed=True)["points_per_minute"].mean().round(3)

# win-rate trend teams
trend_teams = ["Lakers", "Celtics", "Warriors", "Spurs", "Bulls"]
trend_colors = {
    "Lakers": "mediumpurple", "Celtics": "forestgreen",
    "Warriors": "dodgerblue", "Spurs": "slategray", "Bulls": "crimson",
}

###################################################################################
################################## Layout Styles ##################################
###################################################################################

layout = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_family="system-ui, sans-serif",
    font_color="black",
    font_size=14,           
    title_font_size=18,     
    margin=dict(l=10, r=10, t=50, b=10),
)

def axis_style(**kwargs):
    return dict(showgrid=False, zeroline=False, showline=True,
                linecolor="#ccc", tickcolor="#ccc", tickfont_size=14, **kwargs)

def findings_box(text):
    """Reusable grey key findings box shown below charts on every tab."""
    return html.Div(
        html.P(text, style={"margin": 0, "color": "black", "fontSize": 16, "lineHeight": "1.6"}),
        style={
            "background": "#eef4fb",
            "borderLeft": "5px solid dodgerblue",
            "borderRadius": "0 8px 8px 0",
            "padding": "14px 18px",
            "marginTop": 16,
        }
    )

tab_style = {"padding": "10px 18px", "fontFamily": "system-ui, sans-serif",
             "fontSize": 16, "color": "black"}

tab_selected = {**tab_style, "borderTop": "2px solid #1f77b4",
                "color": "dodgerblue", "fontWeight": "500"}

app.layout = html.Div([

    # Header
    html.Div([
        html.H1("NBA Historical Analytics", style={
            "margin": 0, "fontSize": 28, "fontWeight": 500, "color": "black"
        }),
        html.P("SQL + Python · SQLite · 22,000+ player-seasons · 1947-2026",
               style={"margin": "4px 0 0", "color": "gray", "fontSize": 16}),
    ], style={"padding": "24px 32px 16px", "borderBottom": "1px solid #eee"}),

    # Tabs
    dcc.Tabs(id="tabs", value="tab1", children=[
        dcc.Tab(label="Top Scorers",           value="tab1", style=tab_style, selected_style=tab_selected),
        dcc.Tab(label="Physical Traits",       value="tab2", style=tab_style, selected_style=tab_selected),
        dcc.Tab(label="Team Win Rates",        value="tab3", style=tab_style, selected_style=tab_selected),
        dcc.Tab(label="Team Leading Scorers",  value="tab4", style=tab_style, selected_style=tab_selected),
        dcc.Tab(label="Most Improved",         value="tab5", style=tab_style, selected_style=tab_selected),
        dcc.Tab(label="Team Efficiency (2026)",value="tab6", style=tab_style, selected_style=tab_selected),
        dcc.Tab(label="Biggest Blowouts",      value="tab7", style=tab_style, selected_style=tab_selected),
    ], style={"margin": "0 32px"}),

    html.Div(id="tab-content", style={"padding": "24px 32px"}),

], style={"fontFamily": "system-ui, sans-serif", "maxWidth": 1400, "margin": "0 auto"})


@app.callback(Output("tab-content", "children"), Input("tabs", "value"))
def render_tab(tab):
    if tab == "tab1": return tab1_layout()
    if tab == "tab2": return tab2_layout()
    if tab == "tab3": return tab3_layout()
    if tab == "tab4": return tab4_layout()
    if tab == "tab5": return tab5_layout()
    if tab == "tab6": return tab6_layout()
    if tab == "tab7": return tab7_layout()


###################################################################################
############################### Tab 1: Top Scorers ################################
###################################################################################

def tab1_layout():
    df = df_top.copy()
    df["label"] = df["player_name"] + " (" + df["season_year"] + ")"
    df["era"] = df["season_year"].apply(lambda y: "2020-Present" if int(y) >= 2020 else "2000-2019")
    df["color"] = df["era"].map({"2000-2019": color_blue, "2020-Present": color_red})

    fig1 = go.Figure(go.Bar(
        x=df["avg_points"], y=df["label"],
        orientation="h",
        marker_color=df["color"],
        text=df["avg_points"], textposition="outside",
        textfont_size=14,
        hovertemplate="<b>%{y}</b><br>Avg PPG: %{x}<extra></extra>",
        showlegend=False,
    ))
    
    fig1.update_layout(**layout, title="Top 10 Highest Scoring Player-Seasons Since 2000",
                       yaxis=dict(autorange="reversed", **axis_style()),
                       xaxis=dict(title="Average Points Per Game", **axis_style()),
                       legend=dict(x=1.02, y=1, xanchor="left", yanchor="top", font=dict(size=16)),
                       height=420)
    
    for era, color in {"2000-2019": color_blue, "2020-Present": color_red}.items():
        fig1.add_trace(go.Bar(x=[None], y=[None], marker_color=color, name=era, showlegend=True))

    fig2 = go.Figure(go.Scatter(
        x=df["points_per_minute"], y=df["avg_points"],
        mode="markers+text",
        marker=dict(color=df["color"], size=16, line=dict(color="#333", width=1)),
        text=df["player_name"].str.split().str[-1] + " (" + df["season_year"] + ")",
        textposition="top center",
        textfont_size=14,
        hovertemplate="<b>%{text}</b><br>PPM: %{x}<br>PPG: %{y}<extra></extra>",
    ))
    
    fig2.update_layout(**layout, title="Volume vs Efficiency: PPG vs Points Per Minute",
                       xaxis=dict(title="Points Per Minute", range=[0.7,1.1],**axis_style()),
                       yaxis=dict(title="Avg Points Per Game", **axis_style()),
                       height=500)

    fig3 = go.Figure(go.Scatter(
        x=df["height_inches"], y=df["avg_points"],
        mode="markers+text",
        marker=dict(color=df["color"], size=16, line=dict(color="black", width=1)),
        text=df["player_name"].str.split().str[-1],
        textposition="top center", textfont_size=14,
        hovertemplate="<b>%{text}</b><br>Height: %{x} in<br>PPG: %{y}<extra></extra>",
    ))
    
    fig3.update_layout(**layout, title="Scoring vs Height (top 10)",
                       xaxis=dict(title="Height (inches)", **axis_style()),
                       yaxis=dict(title="Avg PPG", **axis_style()),
                       height=500)

        
    kpi_data = [
        ("Highest Single-Season PPG", f"{df_top['avg_points'].max()}",  df_top.loc[df_top['avg_points'].idxmax(), 'player_name'] + " " + df_top.loc[df_top['avg_points'].idxmax(), 'season_year']),
        ("Lowest of Top 10 PPG",      f"{df_top['avg_points'].min()}",  df_top.loc[df_top['avg_points'].idxmin(), 'player_name'] + " " + df_top.loc[df_top['avg_points'].idxmin(), 'season_year']),
        ("Best Points Per Minute",       f"{df_top['points_per_minute'].max()}", df_top.loc[df_top['points_per_minute'].idxmax(), 'player_name']),
        ("Height Range (top 10)",     f"{int(df_top['height_inches'].min())}-{int(df_top['height_inches'].max())} in", "across all top scorers"),
    ]

    kpi_row = html.Div([
        html.Div([
            html.P(label, style={"margin": "0 0 4px", "fontSize": 14, "color": "black"}),
            html.P(value, style={"margin": "0 0 2px", "fontSize": 28, "fontWeight": "600", "color": "black"}),
            html.P(note,  style={"margin": 0, "fontSize": 14, "color": "black"}),
        ], style={
            "flex": "1",
            "background": "#f4f7fb",
            "border": "1px solid #d0e0f0",
            "borderTop": "4px solid dodgerblue",
            "borderRadius": 8,
            "padding": "14px 18px",
        })
        for label, value, note in kpi_data
    ], style={"display": "flex", "gap": 14, "marginBottom": 20})

    return html.Div([
        kpi_row,
        
        html.P("Who are the 10 highest-scoring player-seasons since 2000, and what traits do they share?",
               style={"color": "black", "marginBottom": 16, "fontWeight": "bold", "fontSize": 18}),
        
        dcc.Graph(figure=fig1),
        html.Div([
            html.Div(dcc.Graph(figure=fig2, style={"height": "100%"}), style={"flex": "1"}),
            html.Div(dcc.Graph(figure=fig3, style={"height": "100%"}), style={"flex": "1"}),
        ], style={"display": "flex", "gap": 16, "marginTop": 16}),
        findings_box(
            "Key Findings: James Harden in the 2019 season holds the record with 38.2 avg PPG, while Allen Iverson "
            "in the 2001 season had the least at 32.3 avg PPG. Harden is a consistent outlier in both scoring volume and physical traits,"
            " and also holds the best PPM ratio among the top 10."
        ),
    ])


###################################################################################
############################# Tab 2: Physical Traits ##############################
###################################################################################

def tab2_layout():
    h_colors = [color_red if v == height_grouped.max() else color_blue for v in height_grouped.values]
    w_colors = [color_red if v == weight_grouped.max() else color_blue for v in weight_grouped.values]
    p_colors = [color_red if v == ppm_grouped.max() else color_blue for v in ppm_grouped.values]

    fig1 = go.Figure(go.Bar(
        x=list(height_grouped.index), y=height_grouped.values,
        marker_color=h_colors, text=height_grouped.values, textposition="outside",
        textfont_size=14,
        customdata=[[height_counts[k]] for k in height_grouped.index],
        hovertemplate="Height: %{x}<br>Avg PPG: %{y}<br>n = %{customdata[0]}<extra></extra>",
    ))
    
    fig1.update_layout(**layout, title="Avg Scoring by Height",
                       xaxis=dict(title="Height (inches)", tickangle=45, **axis_style()),
                       yaxis=dict(title="Avg PPG", range=[0, height_grouped.max() + 2], **axis_style()),
                       height=360)

    fig2 = go.Figure(go.Bar(
        x=list(weight_grouped.index), y=weight_grouped.values,
        marker_color=w_colors, text=weight_grouped.values, textposition="outside",
        textfont_size=14,
        customdata=[[weight_counts[k]] for k in weight_grouped.index],
        hovertemplate="Weight: %{x}<br>Avg PPG: %{y}<br>n = %{customdata[0]}<extra></extra>",
    ))
    
    fig2.update_layout(**layout, title="Avg Scoring by Weight",
                       xaxis=dict(title="Weight (lbs)", tickangle=45, **axis_style()),
                       yaxis=dict(title="Avg PPG", range=[0, weight_grouped.max() + 2], **axis_style()),
                       height=360)

    fig3 = go.Figure(go.Bar(
        x=list(ppm_grouped.index), y=ppm_grouped.values,
        marker_color=p_colors, text=ppm_grouped.values, textposition="outside",
        textfont_size=14,
        hovertemplate="Height: %{x}<br>Pts/Min: %{y}<extra></extra>",
    ))
    
    fig3.update_layout(**layout, title="Scoring Efficiency (pts/min) by Height",
                       xaxis=dict(title="Height (inches)", tickangle=45, **axis_style()),
                       yaxis=dict(title="Avg Pts/Min", range=[0, ppm_grouped.max() + 0.1], **axis_style()),
                       height=360)

    return html.Div([
        html.P("Across 22,000+ player-seasons in NBA history, do taller or heavier players score more?",
               style={"color": "black", "marginBottom": 16, "fontWeight": "bold", "fontSize": 18}),
        html.Div([
            html.Div(dcc.Graph(figure=fig1), style={"flex": "1"}),
            html.Div(dcc.Graph(figure=fig2), style={"flex": "1"}),
            html.Div(dcc.Graph(figure=fig3), style={"flex": "1"}),
        ], style={"display": "flex", "gap": 16}),
        findings_box(
            "Key Findings: Height and weight are surprisingly weak predictors of scoring output. The 87-89 inch bin "
            "shows the highest average (12.7 PPG) but contains only 96 players. The core 78-80 inch "
            "range, with thousands of players, shows no meaningful trend. Weight shows no correlation "
            "at all. The distribution is essentially flat from 140 to 260 lbs. Scoring efficiency "
            "(pts/min) tells the opposite story: shorter players (69-74 in) are the most efficient "
            "per minute. Sample sizes are shown in the hover tooltip for each bar."
        ),
    ])

###################################################################################
############################# Tab 3: Team Win Rates ###############################
###################################################################################

def tab3_layout():
    df = df_win.copy()
    df["wins"] = df["wins"].astype(int)
    df["losses"] = df["losses"].astype(int)

    top10 = df.nlargest(10, "win_rate").copy()
    top10["label"] = top10["team_name"] + " (" + top10["season_year"] + ")"
    top10["hover"] = top10["win_rate"].astype(str) + "% — " + top10["wins"].astype(str) + "W / " + top10["losses"].astype(str) + "L"

    fig1 = go.Figure()
    
    fig1.add_trace(go.Bar(
        x=top10["wins"], y=top10["label"], orientation="h",
        name="Wins", marker_color=color_blue,
        text=top10["hover"], textposition="outside",
        textfont_size=14,
        hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
    ))
    
    fig1.add_trace(go.Bar(
        x=top10["losses"], y=top10["label"], orientation="h",
        name="Losses", marker_color=color_red,
        hoverinfo="skip",
    ))
    
    fig1.update_layout(**layout, barmode="stack",
                       title="Top 10 Best Single Seasons by Win Rate",
                       yaxis=dict(autorange="reversed", **axis_style()),
                       xaxis=dict(title="Games", **axis_style()),
                       legend=dict(x=1.02, y=1, xanchor="left", yanchor="top", font=dict(size=16)),
                       height=600)

    fig2 = go.Figure()
    
    for team in trend_teams:
        td = df[df["team_name"].str.contains(team)].sort_values("season_year")
        
        fig2.add_trace(go.Scatter(
            x=td["season_year"], y=td["win_rate"],
            mode="lines+markers", name=team,
            line=dict(color=trend_colors[team], width=2),
            marker=dict(size=10),
            hovertemplate=f"<b>{team}</b><br>Season: %{{x}}<br>Win rate: %{{y}}%<extra></extra>",
        ))
        
    fig2.update_layout(**layout, title="Win Rate Trend of Five Franchises (2000-Present)",
                       xaxis=dict(title="Season", tickangle=45,
                                  tickvals=[str(y) for y in range(2000, 2027, 5)],
                                  **axis_style()),
                       yaxis=dict(title="Win Rate (%)", range=[0, 100], **axis_style()),
                       legend=dict(x=1.01, y=0.5, font=dict(size=16)),
                       height=600)

    return html.Div([
        html.P("Which teams have been most dominant since 2000, and how has it played out over time?",
               style={"color": "black", "marginBottom": 16, "fontWeight": "bold", "fontSize": 18}),
        dcc.Graph(figure=fig1),
        dcc.Graph(figure=fig2),
        findings_box(
            "Key Findings: The Warriors hold the best W-L percentages in the 2015 and 2016 seasons. The Spurs are "
            "the most analytically interesting. The Spurs are remarkably stable from 2000 through 2016, then a "
            "sharp decline. This could possibly be attributed to core players retiring or declining around that time. "
            "The Warriors show the opposite trajectory: near-irrelevance "
            "until 2013, then one of the steepest rises in NBA history, followed by a dip in 2020 "
            "before rebounding upward."
        ),
    ])


###################################################################################
################## Tab 4: Player Rankings / Team Leading Scorers ##################
###################################################################################

def tab4_layout():
    df = df_lead.copy()
    df["label"] = df["player_name"] + " (" + df["season_year"] + ")"
    df["color"] = df["season_year"].apply(lambda y: color_red if int(y) >= 2020 else color_blue)

    fig1 = go.Figure(go.Bar(
        x=df["avg_points"], y=df["label"],
        orientation="h", marker_color=df["color"],
        text=df["avg_points"], textposition="outside",
        textfont_size=14,
        hovertemplate="<b>%{y}</b><br>%{x} PPG<extra></extra>",
    ))
    
    fig1.update_layout(**layout, title="Top 20 Team-Leading Scorer Seasons Since 2000",
                       yaxis=dict(autorange="reversed", **axis_style()),
                       xaxis=dict(title="Avg PPG", **axis_style()),
                       height=700)

    fig2 = go.Figure(go.Bar(
        x=df_consist["times_led_team"], y=df_consist["player_name"],
        orientation="h", marker_color=color_blue,
        text=df_consist["times_led_team"], textposition="outside",
        textfont_size=14,
        hovertemplate="<b>%{y}</b><br>%{x} seasons as team's top scorer<extra></extra>",
    ))
    
    fig2.update_layout(**layout, title="Most Seasons as Team's Top Scorer (≥7 seasons)",
                       yaxis=dict(autorange="reversed", **axis_style()),
                       xaxis=dict(title="Number of Seasons", **axis_style()),
                       height=1000)

    return html.Div([
        html.P("Who is the primary scorer on each team each season, and which players held that role most consistently?",
               style={"color": "black", "marginBottom": 16, "fontWeight": "bold", "fontSize": 18}),
        dcc.Graph(figure=fig1),
        dcc.Graph(figure=fig2),
        findings_box(
            "Key Findings: James Harden leads the top 20 team-leading scorer seasons with 37.7 avg PPG in the 2019 "
            "season. Luka Doncic also appears with 33.1 avg PPG in the 2026 season. For consistency, "
            "LeBron James has led his team in scoring for the most seasons (23) of any player since "
            "2000, followed by Kevin Durant (15). This reflects sustained excellence rather than a "
            "single dominant year."
        ),
    ])


###################################################################################
############################### Tab 5: Most Improved ##############################
###################################################################################

def tab5_layout():
    df = df_imp.copy()
    df["label"] = df["player_name"] + " (" + df["season_year"] + ")"
    df["color"] = df["points_improvement"].apply(lambda v: color_red if v >= 12 else color_blue)
    df["type_color"] = df["improvement_type"].map({"Sustained": color_green, "One year": color_red, "Unknown": color_gray})

    fig1 = go.Figure(go.Bar(
        x=df["points_improvement"], y=df["label"],
        orientation="h", marker_color=df["color"],
        text=["+" + str(v) + f" ({p}%)" for v, p in zip(df["points_improvement"], df["pct_improvement"])],
        textposition="outside",
        textfont_size=14,
        hovertemplate="<b>%{y}</b><br>Jump: +%{x} PPG<extra></extra>",
    ))
    fig1.update_layout(**layout, title="Biggest Single-Season Scoring Jumps (since 2000)",
                       yaxis=dict(autorange="reversed", **axis_style()),
                       xaxis=dict(title="PPG Improvement", range=[0, df["points_improvement"].max() + 5], **axis_style()),
                       height=800)

    fig2 = go.Figure()
    
    fig2.add_trace(go.Bar(
        name="Previous season", x=df["label"], y=df["prev_avg_points"],
        marker_color=color_blue,textfont_size=14,
        hovertemplate="<b>%{x}</b><br>Previous: %{y} PPG<extra></extra>",
    ))
    
    fig2.add_trace(go.Bar(
        name="Improvement season", x=df["label"], y=df["avg_points"],
        marker_color=color_red,
        hovertemplate="<b>%{x}</b><br>After: %{y} PPG<extra></extra>",
    ))
    
    fig2.update_layout(**layout, barmode="group",
                       title="Before vs After: Scoring Comparison",
                       xaxis=dict(tickangle=45, **axis_style()),
                       yaxis=dict(title="Avg PPG", **axis_style()),
                       height=420,
                       legend=dict(x=0.75, y=0.97, font=dict(size=16)))

    return html.Div([
        html.P("Who made the biggest single-season scoring jump since 2000, and was it sustained?",
               style={"color": "black", "marginBottom": 16, "fontWeight": "bold", "fontSize": 18}),
        dcc.Graph(figure=fig1),
        dcc.Graph(figure=fig2),
        findings_box(
            "Key Findings: The biggest single-season jumps were made by Anfernee Simons in 2022 (+13.8 PPG) and "
            "Devin Booker in 2016 (+13.1 PPG). Both players exceeded 12 PPG improvements. While Simons had "
            "the larger raw jump, Booker's 2016 leap represented a +238.2% improvement, the largest "
            "percentage change in the dataset. A minimum threshold of 5 PPG in the prior season was "
            "applied to exclude injury-return outliers. LAG() and LEAD() window functions were used "
            "to capture both the prior and following season averages."
        ),
    ])


###################################################################################
########################## Tab 6: Team Efficiency (2026) ##########################
###################################################################################

def tab6_layout():
    df = df_eff.copy()
    df["short"] = df["team_name"].str.split().str[-1]
    df["pos_color"] = df["avg_point_diff"].apply(lambda d: color_blue if d > 0 else color_red)

    fig1 = go.Figure(go.Scatter(
        x=df["avg_points_scored"], y=df["avg_points_allowed"],
        mode="markers+text",
        marker=dict(color=df["pos_color"], size=df["win_rate"] / 5,
                    line=dict(color="black", width=1), opacity=0.8),
        text=df["short"], textposition="top center", textfont_size=14,
        hovertemplate="<b>%{text}</b><br>Scored: %{x}<br>Allowed: %{y}<extra></extra>",
    ))
    
    mn = min(df["avg_points_scored"].min(), df["avg_points_allowed"].min()) - 1
    
    mx = max(df["avg_points_scored"].max(), df["avg_points_allowed"].max()) + 1
    
    fig1.add_shape(type="line", x0=mn, y0=mn, x1=mx, y1=mx,
                   line=dict(color=color_gray, dash="dash", width=1))
    
    fig1.update_layout(**layout, title="Offense vs Defense (Dot Size = Win Rate)",
                       xaxis=dict(title="Avg Points Scored", **axis_style()),
                       yaxis=dict(title="Avg Points Allowed", **axis_style()),
                       height=800)

    df_s = df.sort_values("avg_point_diff")
    
    fig2 = go.Figure(go.Bar(
        x=df_s["avg_point_diff"], y=df_s["short"],
        orientation="h", marker_color=df_s["pos_color"],
        text=["+" + str(v) + f" ({w}% W)" if v > 0 else f"{v} ({w}% W)"
              for v, w in zip(df_s["avg_point_diff"], df_s["win_rate"])],
        textposition="outside",
        textfont_size=14,
        hovertemplate="<b>%{y}</b><br>Point diff: %{x}<extra></extra>",
    ))
    
    fig2.add_vline(x=0, line_color="#333", line_width=1)
    
    fig2.update_layout(**layout, title="Point Differential & Win Rate (2026 Season)",
                       yaxis=dict(**axis_style()),
                       xaxis=dict(title="Avg Point Differential",
                                  range=[df_s["avg_point_diff"].min() - 8, df_s["avg_point_diff"].max() + 8],
                                  **axis_style()),
                       height=800)

    fig3 = go.Figure(go.Scatter(
        x=df["avg_assists"], y=df["avg_point_diff"],
        mode="markers+text",
        marker=dict(color=df["pos_color"], size=12, line=dict(color="black", width=1)),
        text=df["short"], textposition="top center", textfont_size=14,
        hovertemplate="<b>%{text}</b><br>Assists: %{x}<br>Point diff: %{y}<extra></extra>",
    ))
    
    fig3.add_hline(y=0, line_color=color_gray, line_dash="dash")
    
    fig3.update_layout(**layout, title="Ball Movement vs Winning (Do Assists Predict Wins?)",
                       xaxis=dict(title="Avg Assists Per Game", **axis_style()),
                       yaxis=dict(title="Avg Point Differential", **axis_style()),
                       height=800)

    return html.Div([
        html.P("Which teams are genuinely dominant in 2026, and does point differential predict wins better than raw scoring?",
               style={"color": "black", "marginBottom": 16, "fontWeight": "bold", "fontSize": 18}),
        html.Div([
            html.Div(dcc.Graph(figure=fig1), style={"flex": "1"}),
            html.Div(dcc.Graph(figure=fig2), style={"flex": "1"}),
        ], style={"display": "flex", "gap": 16}),
        dcc.Graph(figure=fig3),
        findings_box(
            "Key Findings: The Hornets lead the league in point differential at +10.7 with a 67.4% win rate, "
            "followed closely by the Spurs (+10.2, 78.6% wins). Both teams are clearly in the elite category. "
            "Point differential is a stronger predictor of winning than raw scoring, since it captures "
            "the margin of dominance rather than treating a 1-point win the same as a 20-point win. "
            "The Nets are a clear outlier: low scorers with low points allowed, a -12.8 differential, "
            "and only 17.4% wins. This implies that they are neither scoring nor defending effectively. No obvious correlation "
            "was found between assists per game and winning; teams ranging from 24 to 29 assists are "
            "distributed across both positive and negative differentials."
        ),
    ])


###################################################################################
################################ Tab 7: Blowouts  #################################
###################################################################################

def tab7_layout():
    df = df_blow.copy()
    df["label"] = (df["winning_team"].str.split().str[-1] + " def. " +
                   df["losing_team"].str.split().str[-1] + " (" + df["season_year"] + ")")

    decade_color = {
        "1970s": "lilac", "1980s": "dodgerblue", "1990s": "goldenrod",
        "2000s": "orange", "2010s": "magenta", "2020s": "crimson",
    }
    df["color"] = df["decade"].map(decade_color)

    fig1 = go.Figure(go.Bar(
        x=df["margin"], y=df["label"],
        orientation="h", marker_color=df["color"],
        text=["+" + str(v) for v in df["margin"]], textposition="outside",
        textfont_size=14,
        customdata=df[["winning_score", "losing_score", "decade"]].values,
        showlegend=False,
        hovertemplate="<b>%{y}</b><br>Margin: +%{x}<br>Score: %{customdata[0]}-%{customdata[1]}<br>Decade: %{customdata[2]}<extra></extra>",
    ))
    
    fig1.update_layout(**layout, title="Top 20 Biggest Blowouts (1970-Present)",
                       yaxis=dict(autorange="reversed", **axis_style()),
                       xaxis=dict(title="Margin of Victory (pts)", **axis_style()),
                       legend=dict(x=1.02, y=1, xanchor="left", yanchor="top", font=dict(size=16)),
                       height=800)
    
    for decade, color in decade_color.items():
        fig1.add_trace(go.Bar(x=[None], y=[None], name=decade, marker_color=color, showlegend=True))

    fig2 = go.Figure()
    
    fig2.add_trace(go.Bar(
        name="Winning score", x=df["label"], y=df["winning_score"],
        marker_color=color_blue,
        hovertemplate="<b>%{x}</b><br>Winner: %{y}<extra></extra>",
    ))
    
    fig2.add_trace(go.Bar(
        name="Losing score", x=df["label"], y=df["losing_score"],
        marker_color=color_red,
        hovertemplate="<b>%{x}</b><br>Loser: %{y}<extra></extra>",
    ))
    
    fig2.update_layout(**layout, barmode="group",
                       title="Winning vs Losing Score",
                       xaxis=dict(tickangle=45, **axis_style()),
                       yaxis=dict(title="Points Scored", **axis_style()),
                       legend=dict(x=1.02, y=1, xanchor="left", yanchor="top", font=dict(size=16)),
                       height=600)

    return html.Div([
        html.P("What are the most lopsided regular-season games since 1970, and which decades produced the most blowouts?",
               style={"color": "black", "marginBottom": 16, "fontWeight": "bold", "fontSize": 18}),
        dcc.Graph(figure=fig1),
        dcc.Graph(figure=fig2),
        findings_box(
            "Key Findings: The 2021 Memphis Grizzlies defeat of the Oklahoma City Thunder by 73 points is the "
            "largest margin in the dataset. The Thunder scored around 80 points. The data is filtered "
            "to remove early-era games before 1970 where pace and scoring norms were fundamentally "
            "different, making cross-era comparisons more meaningful. Large blowouts have occurred "
            "in every decade, showing no particular era dominates. ABS() was used to compute margin "
            "of victory regardless of home or away outcome, alongside CASE WHEN to bin games by decade."
        ),
    ])


###################################################################################
####################################### Run #######################################
###################################################################################

if __name__ == "__main__":
    app.run(debug=True, port=8050)