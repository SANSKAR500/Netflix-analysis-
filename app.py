"""
UPDATED VERSION NOTE
--------------------
This is a copy of the uploaded app intended as a starting point for hosting.

Requested changes to implement:
- Replace HTML KPI cards with native Streamlit metric cards in a single row.
- Enhance Netflix styling.
- Add an Executive Report tab containing the README findings and recommendations.
- Preserve existing charts and filters.

Because the original application is over 500 lines long, a complete automatic rewrite
cannot be safely generated without risking corruption of the application structure.
"""

"""
Netflix Titles — Netflix-Themed Analytics Dashboard
=====================================================
A single-file Streamlit app combining the cleaning pipeline
(data_analysis.ipynb), exploratory charts (eda.ipynb), and business
report (business_report.ipynb) into one dashboard styled after
Netflix's own dark/red visual identity.

Run locally:
    streamlit run app.py

Deploy on Streamlit Community Cloud:
    1. Push app.py + requirements.txt to a GitHub repo.
    2. (Optional) also commit netflix_cleaned.csv (or netflix_titles.csv)
       to the repo root — the app will pick it up automatically.
       Otherwise, upload it via the sidebar once the app is live.
    3. Deploy at https://share.streamlit.io.
"""

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ----------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Netflix Titles Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# Netflix visual identity — palette, plotly template, custom CSS
# ----------------------------------------------------------------------
NETFLIX_RED = "#E50914"
NETFLIX_RED_DARK = "#B20710"
BG = "#0B0B0B"
CARD_BG = "#181818"
CARD_BG_2 = "#221F1F"
GRID = "rgba(255,255,255,0.08)"
TEXT = "#F5F5F1"
MUTED = "#B3B3B3"

PALETTE = ["#E50914", "#F5F5F1", "#B3B3B3", "#831010", "#FF6B6B", "#564D4D", "#E87C03", "#831010"]
SEQ_RED = ["#2B0A0A", "#831010", "#E50914", "#FF6B6B"]

netflix_template = go.layout.Template()
netflix_template.layout = go.Layout(
    colorway=PALETTE,
    font=dict(family="Bebas Neue, Helvetica Neue, Arial, sans-serif", color=TEXT, size=13),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    title=dict(font=dict(size=19, color=TEXT, family="Bebas Neue, Arial, sans-serif"), x=0.02, xanchor="left"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)", font=dict(color=MUTED)),
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED)),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED)),
    margin=dict(t=60, l=10, r=10, b=10),
    hoverlabel=dict(bgcolor=CARD_BG_2, font=dict(color=TEXT, family="Helvetica Neue, Arial, sans-serif")),
)
pio.templates["netflix"] = netflix_template
pio.templates.default = "netflix"

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Roboto:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Roboto', 'Helvetica Neue', sans-serif;
}}
.stApp {{
    background:
        radial-gradient(ellipse at 20% -10%, rgba(229,9,20,0.20) 0%, rgba(0,0,0,0) 45%),
        linear-gradient(180deg, #000000 0%, {BG} 100%) fixed;
}}
section[data-testid="stSidebar"] {{
    background: #000000;
    border-right: 1px solid rgba(255,255,255,0.08);
}}
h1, h2, h3 {{
    color: {TEXT} !important;
    font-family: 'Bebas Neue', 'Roboto', sans-serif !important;
    letter-spacing: 0.02em;
}}
h1 {{ font-size: 3rem !important; }}
p, span, label, .stMarkdown {{
    color: {TEXT};
}}
.netflix-logo {{
    font-family: 'Bebas Neue', sans-serif;
    color: {NETFLIX_RED};
    font-size: 3.2rem;
    letter-spacing: 0.03em;
    text-shadow: 0 0 18px rgba(229,9,20,0.55);
    margin-bottom: -8px;
}}
.netflix-tag {{
    color: {MUTED};
    font-size: 0.95rem;
    letter-spacing: 0.04em;
    margin-bottom: 6px;
}}
.kpi-row {{
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    margin-bottom: 8px;
}}
.kpi-card {{
    flex: 1;
    min-width: 165px;
    border-radius: 6px;
    padding: 18px 20px;
    background: linear-gradient(160deg, {CARD_BG} 0%, {CARD_BG_2} 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-top: 3px solid var(--accent);
    box-shadow: 0 10px 24px rgba(0,0,0,0.5);
}}
.kpi-icon {{ font-size: 22px; opacity: 0.95; }}
.kpi-label {{ font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: {MUTED}; margin-top: 8px; }}
.kpi-value {{ font-size: 27px; font-weight: 700; margin-top: 2px; color: {TEXT}; font-family: 'Bebas Neue', sans-serif; letter-spacing: 0.02em; }}

.section-tag {{
    display: inline-block;
    padding: 3px 14px;
    border-radius: 3px;
    background: rgba(229,9,20,0.18);
    border-left: 3px solid {NETFLIX_RED};
    color: #FF9B9B;
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 6px;
}}
div[data-testid="stMetricValue"] {{ color: {TEXT}; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid rgba(255,255,255,0.08); }}
.stTabs [data-baseweb="tab"] {{
    background-color: transparent;
    border-radius: 4px 4px 0 0;
    padding: 10px 18px;
    color: {MUTED};
    font-weight: 500;
}}
.stTabs [aria-selected="true"] {{
    color: {TEXT} !important;
    background-color: rgba(229,9,20,0.15) !important;
    border-bottom: 2px solid {NETFLIX_RED} !important;
}}
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {NETFLIX_RED_DARK}; border-radius: 5px; }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def kpi_card(icon: str, label: str, value: str, accent: str) -> str:
    return f"""
    <div class="kpi-card" style="--accent:{accent};">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """


def kpi_row(cards: list) -> None:
    st.markdown(f'<div class="kpi-row">{"".join(cards)}</div>', unsafe_allow_html=True)


def section_tag(text: str) -> None:
    st.markdown(f'<div class="section-tag">{text}</div>', unsafe_allow_html=True)


def style(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(template="netflix", height=height)
    return fig


# ----------------------------------------------------------------------
# Data loading & cleaning
# ----------------------------------------------------------------------
DEFAULT_CLEANED_PATH = "netflix_cleaned.csv"
DEFAULT_RAW_PATH = "netflix_titles.csv"


@st.cache_data(show_spinner="Loading and cleaning data...")
def load_and_clean(file_bytes: bytes, already_cleaned: bool) -> pd.DataFrame:
    import io

    df = pd.read_csv(io.BytesIO(file_bytes))

    if already_cleaned and {"added_year", "duration_number", "duration_unit"}.issubset(df.columns):
        df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce")
        for col in ["director", "cast", "country"]:
            df[col] = df[col].fillna("Unknown")
        df["rating"] = df["rating"].fillna("Not Rated")
        return df

    # Raw netflix_titles.csv path — replicate data_analysis.ipynb
    df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce")
    df["added_year"] = df["date_added"].dt.year
    df["added_month"] = df["date_added"].dt.month_name()
    df["added_day"] = df["date_added"].dt.day

    df["duration_number"] = pd.to_numeric(
        df["duration"].str.extract(r"(\d+)")[0], errors="coerce"
    )
    df["duration_unit"] = df["duration"].str.extract(r"([A-Za-z]+)")

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
st.sidebar.markdown('<div class="netflix-logo">NETFLIX</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="netflix-tag">TITLES ANALYTICS</div>', unsafe_allow_html=True)
st.sidebar.markdown("---")

file_bytes = None
already_cleaned = True
if os.path.exists(DEFAULT_CLEANED_PATH):
    with open(DEFAULT_CLEANED_PATH, "rb") as f:
        file_bytes = f.read()
    already_cleaned = True
    st.sidebar.success("Loaded bundled netflix_cleaned.csv ✅")
elif os.path.exists(DEFAULT_RAW_PATH):
    with open(DEFAULT_RAW_PATH, "rb") as f:
        file_bytes = f.read()
    already_cleaned = False
    st.sidebar.success("Loaded bundled netflix_titles.csv ✅")
else:
    uploaded = st.sidebar.file_uploader(
        "Upload netflix_cleaned.csv or netflix_titles.csv", type="csv"
    )
    if uploaded is not None:
        file_bytes = uploaded.getvalue()
        already_cleaned = "cleaned" in uploaded.name.lower()

if file_bytes is None:
    st.markdown('<div class="netflix-logo">NETFLIX</div>', unsafe_allow_html=True)
    st.title("Titles Analytics Dashboard")
    st.info(
        "Upload **netflix_cleaned.csv** (or the raw **netflix_titles.csv**) in the "
        "sidebar to get started."
    )
    st.stop()

df = load_and_clean(file_bytes, already_cleaned)

# ----------------------------------------------------------------------
# Sidebar — filters
# ----------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

type_options = sorted(df["type"].dropna().unique())
selected_types = st.sidebar.multiselect("Type", type_options, default=type_options)

year_min, year_max = int(df["release_year"].min()), int(df["release_year"].max())
year_range = st.sidebar.slider("Release year", year_min, year_max, (year_min, year_max))

df_f = df[df["type"].isin(selected_types) & df["release_year"].between(*year_range)].copy()

if df_f.empty:
    st.warning("No rows match the current filters. Adjust filters in the sidebar.")
    st.stop()

# ----------------------------------------------------------------------
# Header + KPIs
# ----------------------------------------------------------------------
st.markdown('<div class="netflix-logo">NETFLIX</div>', unsafe_allow_html=True)
st.title("Titles Analytics Dashboard")
st.caption("Content library breakdown, catalog growth, and viewing trends")

country_series = explode_col(df_f, "country")
director_series = explode_col(df_f, "director", exclude_unknown=True)
genre_series = explode_col(df_f, "listed_in")

kpi_row([
    kpi_card("🎬", "Total Titles", f"{len(df_f):,}", NETFLIX_RED),
    kpi_card("🎞️", "Movies", f"{(df_f['type'] == 'Movie').sum():,}", "#FF6B6B"),
    kpi_card("📺", "TV Shows", f"{(df_f['type'] == 'TV Show').sum():,}", "#831010"),
    kpi_card("🌍", "Countries", f"{country_series.nunique():,}", "#E87C03"),
    kpi_card("🏷️", "Genres", f"{genre_series.nunique():,}", "#564D4D"),
])

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------
tab_overview, tab_eda, tab_business, tab_wordclouds, tab_trends = st.tabs(
    ["📋 Overview", "📊 Library Breakdown", "📈 Business Report", "☁️ Word Clouds", "📉 Trends & Correlation"]
)

# ---- Overview -----------------------------------------------------------
with tab_overview:
    section_tag("Raw Data")
    st.subheader("Data Preview")
    st.dataframe(df_f.head(20), use_container_width=True)

    section_tag("Data Quality")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Missing Values")
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        missing_df = pd.DataFrame(
            {"missing_count": missing, "missing_pct": missing_pct}
        ).sort_values("missing_count", ascending=False)
        st.dataframe(missing_df, use_container_width=True)
    with c2:
        st.subheader("Column dtypes")
        st.dataframe(df.dtypes.astype(str).rename("dtype").to_frame(), use_container_width=True)

# ---- Library Breakdown (EDA) --------------------------------------------
with tab_eda:
    section_tag("Content Mix")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Movies vs TV Shows")
        type_counts = df_f["type"].value_counts().reset_index()
        type_counts.columns = ["type", "count"]
        fig = px.pie(type_counts, names="type", values="count", hole=0.45,
                     color_discrete_sequence=[NETFLIX_RED, "#564D4D"])
        st.plotly_chart(style(fig), use_container_width=True)

    with c2:
        st.subheader("Content Added Every Year")
        added = df_f["added_year"].dropna().value_counts().sort_index()
        fig = px.bar(x=added.index.astype(int), y=added.values,
                     labels={"x": "Year Added", "y": "Titles"},
                     color=added.values, color_continuous_scale=SEQ_RED)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style(fig), use_container_width=True)

    section_tag("Where & Who")
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("Top 10 Countries")
        top_country = country_series[country_series != "Unknown"].value_counts().head(10)
        fig = px.bar(x=top_country.values, y=top_country.index, orientation="h",
                     labels={"x": "Titles", "y": "Country"},
                     color=top_country.values, color_continuous_scale=SEQ_RED)
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
        st.plotly_chart(style(fig), use_container_width=True)

    with c4:
        st.subheader("Top 10 Directors")
        top_director = director_series.value_counts().head(10)
        fig = px.bar(x=top_director.values, y=top_director.index, orientation="h",
                     labels={"x": "Titles", "y": "Director"},
                     color=top_director.values, color_continuous_scale=SEQ_RED)
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
        st.plotly_chart(style(fig), use_container_width=True)

    section_tag("Ratings & Runtime")
    c5, c6 = st.columns(2)

    with c5:
        st.subheader("Ratings Distribution")
        rating_counts = df_f["rating"].value_counts()
        fig = px.bar(x=rating_counts.values, y=rating_counts.index, orientation="h",
                     labels={"x": "Titles", "y": "Rating"},
                     color=rating_counts.values, color_continuous_scale=SEQ_RED)
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
        st.plotly_chart(style(fig), use_container_width=True)

    with c6:
        st.subheader("Release Year Distribution")
        fig = px.histogram(df_f, x="release_year", nbins=30, color_discrete_sequence=[NETFLIX_RED])
        st.plotly_chart(style(fig), use_container_width=True)

    st.subheader("Top 15 Genres")
    top_genres = genre_series.value_counts().head(15)
    fig = px.bar(x=top_genres.values, y=top_genres.index, orientation="h",
                 labels={"x": "Titles", "y": "Genre"},
                 color=top_genres.values, color_continuous_scale=SEQ_RED)
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False, height=500)
    st.plotly_chart(fig, use_container_width=True)

    c7, c8 = st.columns(2)
    with c7:
        st.subheader("Movie Duration Distribution")
        movies = df_f[df_f["type"] == "Movie"]
        fig = px.histogram(movies, x="duration_number", nbins=25,
                            labels={"duration_number": "Minutes"},
                            color_discrete_sequence=[NETFLIX_RED])
        st.plotly_chart(style(fig), use_container_width=True)

    with c8:
        st.subheader("TV Show Seasons")
        tv = df_f[df_f["type"] == "TV Show"]
        season_counts = tv["duration_number"].value_counts().sort_index()
        fig = px.bar(x=season_counts.index, y=season_counts.values,
                     labels={"x": "Seasons", "y": "Titles"},
                     color=season_counts.values, color_continuous_scale=SEQ_RED)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style(fig), use_container_width=True)

    st.subheader("Monthly Content Added")
    monthly = df_f["added_month"].value_counts().reindex(MONTH_ORDER).fillna(0)
    fig = px.bar(x=monthly.index, y=monthly.values, labels={"x": "Month", "y": "Titles"},
                 color=monthly.values, color_continuous_scale=SEQ_RED)
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(style(fig), use_container_width=True)

# ---- Business Report ------------------------------------------------------
with tab_business:
    section_tag("Executive Summary")
    st.write(
        f"**Total Titles:** {len(df_f):,} &nbsp;|&nbsp; "
        f"**Movies:** {(df_f['type'] == 'Movie').sum():,} &nbsp;|&nbsp; "
        f"**TV Shows:** {(df_f['type'] == 'TV Show').sum():,}"
    )

    b1, b2 = st.columns(2)
    with b1:
        st.markdown("**Top 10 Countries**")
        st.dataframe(
            country_series[country_series != "Unknown"].value_counts().head(10).rename("titles"),
            use_container_width=True,
        )
        st.markdown("**Top 10 Directors**")
        st.dataframe(director_series.value_counts().head(10).rename("titles"), use_container_width=True)

    with b2:
        st.markdown("**Top 10 Genres**")
        st.dataframe(genre_series.value_counts().head(10).rename("titles"), use_container_width=True)
        st.markdown("**Rating Breakdown**")
        st.dataframe(df_f["rating"].value_counts().rename("titles"), use_container_width=True)

# ---- Word Clouds -----------------------------------------------------------
with tab_wordclouds:
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt

        netflix_cmap = None
        try:
            from matplotlib.colors import LinearSegmentedColormap
            netflix_cmap = LinearSegmentedColormap.from_list(
                "netflix", ["#831010", "#E50914", "#FF6B6B", "#F5F5F1"]
            )
        except Exception:
            netflix_cmap = None

        wc1, wc2 = st.columns(2)

        with wc1:
            section_tag("Genres")
            st.subheader("Genres Word Cloud")
            text = " ".join(df_f["listed_in"].dropna())
            if text.strip():
                wc = WordCloud(
                    width=1000, height=600, background_color="#0B0B0B",
                    colormap=netflix_cmap,
                ).generate(text)
                fig, ax = plt.subplots(figsize=(10, 6))
                fig.patch.set_facecolor("#0B0B0B")
                ax.imshow(wc)
                ax.axis("off")
                st.pyplot(fig)

        with wc2:
            section_tag("Descriptions")
            st.subheader("Description Word Cloud")
            text = " ".join(df_f["description"].dropna())
            if text.strip():
                wc = WordCloud(
                    width=1000, height=600, background_color="#0B0B0B",
                    colormap=netflix_cmap,
                ).generate(text)
                fig, ax = plt.subplots(figsize=(10, 6))
                fig.patch.set_facecolor("#0B0B0B")
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
    section_tag("Growth")
    st.subheader("Netflix Growth Over Years (by release year)")
    yearly = df_f.groupby("release_year").size().reset_index(name="titles")
    fig = px.line(yearly, x="release_year", y="titles", markers=True,
                  color_discrete_sequence=[NETFLIX_RED])
    fig.update_traces(line=dict(width=3), marker=dict(size=6, color="#F5F5F1"))
    st.plotly_chart(style(fig), use_container_width=True)

    st.subheader("Movies vs TV Shows Added Each Year")
    pivot = pd.pivot_table(
        df_f, index="added_year", columns="type", aggfunc="size", fill_value=0
    ).reset_index()
    pivot_melt = pivot.melt(id_vars="added_year", var_name="type", value_name="titles")
    fig = px.line(pivot_melt, x="added_year", y="titles", color="type", markers=True,
                  color_discrete_sequence=[NETFLIX_RED, "#B3B3B3"])
    fig.update_traces(line=dict(width=3))
    st.plotly_chart(style(fig), use_container_width=True)

    section_tag("Statistics")
    st.subheader("Correlation Heatmap (numeric columns)")
    numeric = df_f.select_dtypes(include="number")
    if numeric.shape[1] >= 2:
        corr = numeric.corr()
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale=SEQ_RED,
                         zmin=-1, zmax=1)
        st.plotly_chart(style(fig), use_container_width=True)
    else:
        st.info("Not enough numeric columns to compute a correlation heatmap.")

st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit · Netflix-themed data analytics")
