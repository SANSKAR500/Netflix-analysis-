"""
Netflix Titles — Interactive Data Analysis Dashboard
=====================================================
Combines the cleaning pipeline (data_analysis.ipynb), exploratory charts
(eda.ipynb), and business report (business_report.ipynb) into one
Streamlit app.

Run locally:
    streamlit run app.py

Deploy on Streamlit Community Cloud:
    1. Push this file + requirements.txt to a GitHub repo.
    2. Go to https://share.streamlit.io, connect the repo, and deploy.
    3. Upload netflix_titles.csv via the sidebar once the app is live
       (or commit it to the repo and load it directly — see NOTE below).
"""

import io

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Netflix Titles Dashboard",
    page_icon="🎬",
    layout="wide",
)

MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


# ----------------------------------------------------------------------
# Data loading & cleaning (mirrors data_analysis.ipynb)
# ----------------------------------------------------------------------
@st.cache_data(show_spinner="Loading and cleaning data...")
def load_and_clean(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(file_bytes))

    # Parse dates
    df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce")
    df["added_year"] = df["date_added"].dt.year
    df["added_month"] = df["date_added"].dt.month_name()
    df["added_day"] = df["date_added"].dt.day

    # Split duration into number + unit
    df["duration_number"] = pd.to_numeric(
        df["duration"].str.extract(r"(\d+)")[0], errors="coerce"
    )
    df["duration_unit"] = df["duration"].str.extract(r"([A-Za-z]+)")

    # Fill missing categoricals
    for col in ["director", "cast", "country"]:
        df[col] = df[col].fillna("Unknown")
    df["rating"] = df["rating"].fillna("Not Rated")

    return df


@st.cache_data(show_spinner=False)
def explode_col(df: pd.DataFrame, col: str, exclude_unknown: bool = False) -> pd.Series:
    subset = df[df[col] != "Unknown"] if exclude_unknown else df
    return subset[col].dropna().str.split(", ").explode()


# ----------------------------------------------------------------------
# Sidebar — data source
# ----------------------------------------------------------------------
st.sidebar.title("🎬 Netflix Dashboard")
uploaded = st.sidebar.file_uploader("Upload netflix_titles.csv", type="csv")

# NOTE: if you commit netflix_titles.csv to your repo, you can skip the
# uploader entirely and instead do:
#   df = load_and_clean(open("netflix_titles.csv", "rb").read())
if uploaded is None:
    st.title("🎬 Netflix Titles Dashboard")
    st.info(
        "Upload **netflix_titles.csv** in the sidebar to get started. "
        "This app cleans the data and reproduces the EDA and business "
        "report visualizations from your notebooks."
    )
    st.stop()

df = load_and_clean(uploaded.getvalue())

# ----------------------------------------------------------------------
# Sidebar — filters
# ----------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

type_options = sorted(df["type"].dropna().unique())
selected_types = st.sidebar.multiselect("Type", type_options, default=type_options)

year_min, year_max = int(df["release_year"].min()), int(df["release_year"].max())
year_range = st.sidebar.slider(
    "Release year", year_min, year_max, (year_min, year_max)
)

df_f = df[
    df["type"].isin(selected_types)
    & df["release_year"].between(*year_range)
].copy()

if df_f.empty:
    st.warning("No rows match the current filters. Adjust filters in the sidebar.")
    st.stop()

# ----------------------------------------------------------------------
# Header KPIs
# ----------------------------------------------------------------------
st.title("🎬 Netflix Titles Dashboard")

country_series = explode_col(df_f, "country")
director_series = explode_col(df_f, "director", exclude_unknown=True)
genre_series = explode_col(df_f, "listed_in")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Titles", f"{len(df_f):,}")
k2.metric("Movies", f"{(df_f['type'] == 'Movie').sum():,}")
k3.metric("TV Shows", f"{(df_f['type'] == 'TV Show').sum():,}")
k4.metric("Countries", f"{country_series.nunique():,}")
k5.metric("Genres", f"{genre_series.nunique():,}")

st.markdown("---")

# ----------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------
tab_overview, tab_eda, tab_business, tab_wordclouds, tab_trends = st.tabs(
    ["📋 Overview", "📊 EDA", "📈 Business Report", "☁️ Word Clouds", "📉 Trends & Correlation"]
)

# ---- Overview ----------------------------------------------------------
with tab_overview:
    st.subheader("Data Preview")
    st.dataframe(df_f.head(20), use_container_width=True)

    st.subheader("Missing Values")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame(
        {"missing_count": missing, "missing_pct": missing_pct}
    ).sort_values("missing_count", ascending=False)
    st.dataframe(missing_df, use_container_width=True)

    st.subheader("Column dtypes")
    st.dataframe(
        df.dtypes.astype(str).rename("dtype").to_frame(), use_container_width=True
    )

# ---- EDA -----------------------------------------------------------------
with tab_eda:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Movies vs TV Shows")
        type_counts = df_f["type"].value_counts().reset_index()
        type_counts.columns = ["type", "count"]
        fig = px.pie(type_counts, names="type", values="count", hole=0.35)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Content Added Every Year")
        added = df_f["added_year"].dropna().value_counts().sort_index()
        fig = px.bar(x=added.index.astype(int), y=added.values,
                     labels={"x": "Year Added", "y": "Titles"})
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        st.subheader("Top 10 Countries")
        top_country = country_series[country_series != "Unknown"].value_counts().head(10)
        fig = px.bar(x=top_country.values, y=top_country.index, orientation="h",
                     labels={"x": "Titles", "y": "Country"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        st.subheader("Top 10 Directors")
        top_director = director_series.value_counts().head(10)
        fig = px.bar(x=top_director.values, y=top_director.index, orientation="h",
                     labels={"x": "Titles", "y": "Director"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    c5, c6 = st.columns(2)

    with c5:
        st.subheader("Ratings Distribution")
        rating_counts = df_f["rating"].value_counts()
        fig = px.bar(x=rating_counts.values, y=rating_counts.index, orientation="h",
                     labels={"x": "Titles", "y": "Rating"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    with c6:
        st.subheader("Release Year Distribution")
        fig = px.histogram(df_f, x="release_year", nbins=30)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 15 Genres")
    top_genres = genre_series.value_counts().head(15)
    fig = px.bar(x=top_genres.values, y=top_genres.index, orientation="h",
                 labels={"x": "Titles", "y": "Genre"})
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
    st.plotly_chart(fig, use_container_width=True)

    c7, c8 = st.columns(2)

    with c7:
        st.subheader("Movie Duration Distribution")
        movies = df_f[df_f["type"] == "Movie"]
        fig = px.histogram(movies, x="duration_number", nbins=25,
                            labels={"duration_number": "Minutes"})
        st.plotly_chart(fig, use_container_width=True)

    with c8:
        st.subheader("TV Show Seasons")
        tv = df_f[df_f["type"] == "TV Show"]
        season_counts = tv["duration_number"].value_counts().sort_index()
        fig = px.bar(x=season_counts.index, y=season_counts.values,
                     labels={"x": "Seasons", "y": "Titles"})
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Monthly Content Added")
    monthly = df_f["added_month"].value_counts().reindex(MONTH_ORDER).fillna(0)
    fig = px.bar(x=monthly.index, y=monthly.values,
                 labels={"x": "Month", "y": "Titles"})
    st.plotly_chart(fig, use_container_width=True)

# ---- Business Report -------------------------------------------------
with tab_business:
    st.subheader("Summary")
    st.write(
        f"**Total Titles:** {len(df_f):,} &nbsp;|&nbsp; "
        f"**Movies:** {(df_f['type'] == 'Movie').sum():,} &nbsp;|&nbsp; "
        f"**TV Shows:** {(df_f['type'] == 'TV Show').sum():,}"
    )

    b1, b2 = st.columns(2)
    with b1:
        st.markdown("**Top 10 Countries**")
        st.dataframe(
            country_series[country_series != "Unknown"]
            .value_counts().head(10).rename("titles"),
            use_container_width=True,
        )
        st.markdown("**Top 10 Directors**")
        st.dataframe(
            director_series.value_counts().head(10).rename("titles"),
            use_container_width=True,
        )

    with b2:
        st.markdown("**Top 10 Genres**")
        st.dataframe(
            genre_series.value_counts().head(10).rename("titles"),
            use_container_width=True,
        )
        st.markdown("**Rating Breakdown**")
        st.dataframe(
            df_f["rating"].value_counts().rename("titles"),
            use_container_width=True,
        )

# ---- Word Clouds -------------------------------------------------------
with tab_wordclouds:
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt

        wc1, wc2 = st.columns(2)

        with wc1:
            st.subheader("Genres Word Cloud")
            text = " ".join(df_f["listed_in"].dropna())
            if text.strip():
                wc = WordCloud(width=1000, height=600, background_color="white").generate(text)
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.imshow(wc)
                ax.axis("off")
                st.pyplot(fig)

        with wc2:
            st.subheader("Description Word Cloud")
            text = " ".join(df_f["description"].dropna())
            if text.strip():
                wc = WordCloud(width=1000, height=600, background_color="white").generate(text)
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.imshow(wc)
                ax.axis("off")
                st.pyplot(fig)
    except ImportError:
        st.warning(
            "The `wordcloud` package isn't installed. Add `wordcloud` to "
            "requirements.txt to enable this tab."
        )

# ---- Trends & Correlation ----------------------------------------------
with tab_trends:
    st.subheader("Netflix Growth Over Years (by release year)")
    yearly = df_f.groupby("release_year").size().reset_index(name="titles")
    fig = px.line(yearly, x="release_year", y="titles", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Movies vs TV Shows Added Each Year")
    pivot = pd.pivot_table(
        df_f, index="added_year", columns="type", aggfunc="size", fill_value=0
    ).reset_index()
    pivot_melt = pivot.melt(id_vars="added_year", var_name="type", value_name="titles")
    fig = px.line(pivot_melt, x="added_year", y="titles", color="type", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Correlation Heatmap (numeric columns)")
    numeric = df_f.select_dtypes(include="number")
    if numeric.shape[1] >= 2:
        corr = numeric.corr()
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                         zmin=-1, zmax=1)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough numeric columns to compute a correlation heatmap.")

st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit • Data cleaning, EDA & business report combined into one app.")
