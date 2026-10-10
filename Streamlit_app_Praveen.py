import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://root:1517@127.0.0.1:3306/tennis_game_analytics")

st.set_page_config(page_title="Tennis Analytics",page_icon="🎾",layout="wide")

st.title("🎾 Tennis Ranking Explorer")
st.subheader("Rankings")
st.sidebar.header("Filters")

query = """
SELECT
    c.competitor_id,
    c.name,
    c.country,
    c.country_code,
    c.abbreviation,
    cr.`rank`,
    cr.movement,
    cr.points,
    cr.competitions_played
FROM competitors c
JOIN competitor_rankings cr
    ON c.competitor_id = cr.competitor_id
"""
query_1 ="""
SELECT
    c.competition_id,
    c.competition_name,
    c.type,
    c.gender,
    cat.category_name
FROM Competitions c
JOIN Categories cat
    ON c.category_id = cat.category_id
"""

query_2 ="""
SELECT
    v.venue_id,
    v.venue_name,
    v.city_name,
    v.country_name,
    v.country_code,
    v.timezone,
    c.complex_name
FROM venues v
JOIN complexes c
    ON v.complex_id = c.complex_id
"""


df = pd.read_sql(query,engine)

df1 = pd.read_sql(query_1,engine)

df2 = pd.read_sql(query_2,engine)

col1,col2,col3,col4 = st.columns(4)

total_competiors = df["competitor_id"].nunique()

total_competition = df1["competition_id"].nunique()

total_countries = df["country"].nunique()

maximum_points = df["points"].max()


with col1:
    st.metric("Total competiors",total_competiors)

with col2:
    st.metric("Total competitions",total_competition)

with col3:
    st.metric("Total countries",total_countries)

with col4:
    st.metric("Highest Point",maximum_points)


st.subheader("Top 10 Competiors")

top_10 = df.sort_values(by="rank").head(10)

st.dataframe(top_10)

# Filters

countries = sorted(df["country"].unique())

selected_country = st.sidebar.selectbox("Country",["All"]+countries)

rank = sorted(df["rank"].unique())

selected_rank = st.sidebar.number_input("Rank",min_value=1,max_value=500,step=1)

gender = df1["gender"].unique()

seleted_gender = st.sidebar.selectbox("Gender",gender)

# Filtered data by Country

st.header("Filtered data by Country")

filtered_df = df.copy()

if selected_country != "ALL":
    filtered_df = filtered_df[filtered_df["country"]==selected_country]

st.dataframe(filtered_df)

# Country Analysis

st.header("🌍 Country Analysis")

country_stats = (
    df.groupby("country")
    .agg(
        competitors=("competitor_id", "nunique"),
        total_points=("points", "sum"),
        average_points=("points", "mean")
    )
    .reset_index()
)

country_stats = country_stats.sort_values(
    "total_points",
    ascending=False
)

st.dataframe(
    country_stats,
    use_container_width=True,
    hide_index=True
)

fig = px.bar(
    country_stats.head(10),
    x="country",
    y="total_points",
    title="Top 10 Countries by Total Ranking Points",
    labels={
        "country": "Country",
        "total_points": "Total Points"
    }
)

st.plotly_chart(
    fig,
    use_container_width=False
)

# Filtered data by Rank

st.header("Filtered data by Rank")

filtered_df1 = df.copy()

if selected_rank !=0:
    filtered_df1 = filtered_df1[filtered_df1["rank"]==selected_rank]

st.dataframe(filtered_df1)

# Points Distribution chart

st.header("📈 Points Distribution")

fig = px.histogram(
    df,
    x="points",
    nbins=20,
    title="Distribution of Competitor Points",
    labels={
        "points": "Ranking Points"
    }
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# Filtered data by gender

st.header("Filtered data by gender")

filtered_df2 = df1.copy()

if seleted_gender !="mixed":
    filtered_df2 = filtered_df2[filtered_df2["gender"]==seleted_gender]


st.dataframe(filtered_df2)

st.header("Complexes and Venues")

st.dataframe(df2)

# Search by competitors

st.header("🔍 Search Competitor")

search_name = st.text_input(
    "Enter competitor name"
)

if search_name:

    search_result = df[
        df["name"].str.contains(
            search_name,
            case=False,
            na=False
        )
    ]

    if len(search_result) > 0:

        st.dataframe(
            search_result[
                [
                    "name",
                    "country",
                    "country_code",
                    "rank",
                    "points",
                    "movement",
                    "competitions_played"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning("No competitor found.")








