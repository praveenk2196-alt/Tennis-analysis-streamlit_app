import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Tennis Intelligence Studio",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# NAVIGATION CONSTANTS
NAV_OVERVIEW = "🏠 Executive Overview"
NAV_COMPETITIONS = "🏆 Competition Analytics"
NAV_VENUES = "🏟️ Venues & Logistics"
NAV_RankINGS = "🎾 Player Rankings"

# Color Palette Definitions (Professional Theme)
PRIMARY_COLOR = "#0F172A"
ACCENT_COLOR = "#2563EB"
BG_COLOR = "#F8FAFC"
CARD_BG = "#FFFFFF"
TEXT_COLOR = "#1E293B"
MUTED_TEXT = "#64748B"
BORDER_COLOR = "#E2E8F0"

# ============================================================
# ADVANCED CUSTOM CSS
# ============================================================
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    /* Global Background */
    .stApp {{
        background-color: {BG_COLOR};
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {PRIMARY_COLOR};
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }}

    section[data-testid="stSidebar"] * {{
        color: #F1F5F9 !important;
    }}

    /* Title Styling */
    .main-header {{
        padding: 10px 0px 25px 0px;
    }}
    .main-title {{
        font-size: 32px;
        font-weight: 800;
        color: {TEXT_COLOR};
        letter-spacing: -0.5px;
    }}
    .main-subtitle {{
        font-size: 15px;
        color: {MUTED_TEXT};
        margin-top: 4px;
    }}

    /* Custom Metric / KPI Cards */
    .kpi-card {{
        background: {CARD_BG};
        border: 1px solid {BORDER_COLOR};
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.08);
    }}
    .kpi-title {{
        font-size: 13px;
        font-weight: 600;
        color: {MUTED_TEXT};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }}
    .kpi-value {{
        font-size: 28px;
        font-weight: 700;
        color: {TEXT_COLOR};
    }}

    /* Tab Customization */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        border-bottom: 1px solid {BORDER_COLOR};
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 45px;
        white-space: pre-wrap;
        border-radius: 8px 8px 0px 0px;
        font-weight: 600;
        font-size: 14px;
        color: {MUTED_TEXT};
    }}
    .stTabs [aria-selected="true"] {{
        color: {ACCENT_COLOR} !important;
        border-bottom: 2px solid {ACCENT_COLOR} !important;
    }}

    /* Section Headers */
    .section-header {{
        font-size: 18px;
        font-weight: 700;
        color: {TEXT_COLOR};
        margin: 20px 0 12px 0;
    }}

    /* Status Pill */
    .status-badge {{
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 13px;
        font-weight: 600;
    }}
    .status-success {{
        background-color: #DCFCE7;
        color: #166534;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# DATA SOURCE INITIALIZATION
# ============================================================
@st.cache_data
def load_data():
    """Load the real Sportradar CSV datasets from the app directory."""
    from pathlib import Path

    data_dir = Path(__file__).resolve().parent

    required_files = {
        "categories": "categories.csv",
        "competitions": "competitions.csv",
        "complexes": "complexes.csv",
        "venues": "venues.csv",
        "competitors": "competitors.csv",
        "Rankings": "competitor_rankings.csv",
    }

    missing = [fileName for fileName in required_files.values()
               if not (data_dir / fileName).exists()]
    if missing:
        raise FileNotFoundError(
            "These CSV files were not found beside app.py: "
            + ", ".join(missing)
            + ". Put all six CSV files in the same folder as app.py."
        )

    categories_df = pd.read_csv(data_dir / required_files["categories"])
    competitions_df = pd.read_csv(data_dir / required_files["competitions"])
    complexes_df = pd.read_csv(data_dir / required_files["complexes"])
    venues_df = pd.read_csv(data_dir / required_files["venues"])
    competitors_df = pd.read_csv(data_dir / required_files["competitors"])
    Rankings_df = pd.read_csv(data_dir / required_files["Rankings"])

    # Keep ID columns as strings: Sportradar IDs such as
    # 'sr:competitor:14898' are identifiers, not numeric values.
    id_columns = [
        (categories_df, ["category_id"]),
        (competitions_df, ["competition_id", "category_id", "parent_id"]),
        (complexes_df, ["complex_id"]),
        (venues_df, ["venue_id", "complex_id"]),
        (competitors_df, ["Competitor_id"]),
        (Rankings_df, ["Competitor_id"]),
    ]
    for df, columns in id_columns:
        for column in columns:
            if column in df.columns:
                df[column] = df[column].astype("string").str.strip()
                df[column] = df[column].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})

    # Convert analytical fields to numeric values in case CSV inference varies.
    for column in ["Rank", "Movement", "Points", "Competitions_played"]:
        if column in Rankings_df.columns:
            Rankings_df[column] = pd.to_numeric(Rankings_df[column], errors="coerce")

    return categories_df, competitions_df, complexes_df, venues_df, competitors_df, Rankings_df

categories_df, competitions_df, complexes_df, venues_df, competitors_df, Rankings_df = load_data()

# Helper for standard Plotly charts layout styling
def apply_chart_theme(fig, height=400):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(family="Inter, sans-serif", color="#334155", size=12),
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", title_font=dict(size=12, color="#64748B")),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title_font=dict(size=12, color="#64748B")),
        hoverlabel=dict(bgcolor="#0F172A", font_size=13, font_family="Inter, sans-serif")
    )
    return fig

# Custom Metric Component Helper
def display_kpi(label: str, value: str):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 10px 0;">
            <div style="font-size: 22px; font-weight: 800; letter-spacing: -0.5px;">🎾 Tennis Studio</div>
            <div style="font-size: 12px; opacity: 0.7; margin-top: 2px;">Sportradar Data Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---")

    page = st.radio(
        "NAVIGATION",
        [
            NAV_OVERVIEW,
            NAV_COMPETITIONS,
            NAV_VENUES,
            NAV_RankINGS
        ],
        index=0
    )

    st.markdown("---")
    
    st.markdown('<span class="status-badge status-success">● Data Ready</span>', unsafe_allow_html=True)

    st.markdown(
        """
        <div style="font-size:12px; color:#94A3B8; margin-top: 30px;">
        <b>Engine:</b> Streamlit + Pandas<br>
        <b>Provider:</b> Sportradar Tennis API
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# PAGE 1: EXECUTIVE OVERVIEW
# ============================================================
if page == NAV_OVERVIEW:
    st.markdown(
        """
        <div class="main-header">
            <div class="main-title">Executive Game Analytics Overview</div>
            <div class="main-subtitle">Comprehensive data overview across global tennis competitions, venues, and players.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    total_categories = len(categories_df)
    total_competitions = len(competitions_df)
    total_venues = len(venues_df)
    total_competitors = len(competitors_df)
    total_countries = competitors_df["Country"].nunique()
    highest_Points = int(Rankings_df["Points"].max())

    st.markdown('<div class="section-header">📊 Executive Overview Metrics</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1: display_kpi("Competitions", f"{total_competitions:,}")
    with col2: display_kpi("Categories", f"{total_categories:,}")
    with col3: display_kpi("Competitors", f"{total_competitors:,}")
    with col4: display_kpi("Venues", f"{total_venues:,}")
    with col5: display_kpi("Countries", f"{total_countries:,}")
    with col6: display_kpi("Top Score", f"{highest_Points:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    # 1. Competitions by Category Chart
    st.markdown('<div class="section-header">🏆 Top Categories by Number of Competitions</div>', unsafe_allow_html=True)
    competition_category_df = categories_df.merge(competitions_df, on="category_id", how="left") \
        .groupby(["category_id", "category_name"], as_index=False) \
        .agg(total_competitions=("competition_id", "count")) \
        .sort_values(by="total_competitions", ascending=False).head(10)

    if not competition_category_df.empty:
        fig_category = px.bar(
            competition_category_df,
            x="category_name",
            y="total_competitions",
            text_auto=True,
            color="total_competitions",
            color_continuous_scale="Blues",
            labels={"category_name": "Category", "total_competitions": "Competitions"}
        )
        fig_category.update_coloraxes(showscale=False)
        apply_chart_theme(fig_category, height=380)
        st.plotly_chart(fig_category, use_container_width=True)

    # 2. Two Column Geographical Layout
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown('<div class="section-header">🌍 Top 10 Countries by Venue Count</div>', unsafe_allow_html=True)
        venue_Country_df = venues_df.groupby("country_name", as_index=False) \
            .agg(total_venues=("venue_id", "count")) \
            .sort_values(by="total_venues", ascending=False).head(10)

        if not venue_Country_df.empty:
            fig_venues = px.bar(
                venue_Country_df,
                x="total_venues",
                y="country_name",
                orientation="h",
                text_auto=True,
                color="total_venues",
                color_continuous_scale="Teal",
                labels={"country_name": "Country", "total_venues": "Venues"}
            )
            fig_venues.update_coloraxes(showscale=False)
            fig_venues.update_layout(yaxis=dict(autorange="reversed"))
            apply_chart_theme(fig_venues, height=380)
            st.plotly_chart(fig_venues, use_container_width=True)

    with col_right:
        st.markdown('<div class="section-header">🎾 Top 10 Countries by Competitor Count</div>', unsafe_allow_html=True)
        competitor_Country_df = competitors_df.groupby("Country", as_index=False) \
            .agg(total_competitors=("Competitor_id", "count")) \
            .sort_values(by="total_competitors", ascending=False).head(10)

        if not competitor_Country_df.empty:
            fig_competitors = px.bar(
                competitor_Country_df,
                x="total_competitors",
                y="Country",
                orientation="h",
                text_auto=True,
                color="total_competitors",
                color_continuous_scale="Viridis",
                labels={"Country": "Country", "total_competitors": "Competitors"}
            )
            fig_competitors.update_coloraxes(showscale=False)
            fig_competitors.update_layout(yaxis=dict(autorange="reversed"))
            apply_chart_theme(fig_competitors, height=380)
            st.plotly_chart(fig_competitors, use_container_width=True)

    # 3. Top Ranked Competitors
    st.markdown('<div class="section-header">⭐ Top 10 Competitors by Ranking Points</div>', unsafe_allow_html=True)
    top_competitors_df = competitors_df.merge(Rankings_df, on="Competitor_id") \
        [["Name", "Country", "Rank", "Points"]] \
        .sort_values(by="Points", ascending=False).head(10)

    if not top_competitors_df.empty:
        st.dataframe(
            top_competitors_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Points": st.column_config.ProgressColumn(
                    "Points",
                    format="%d",
                    min_value=0,
                    max_value=int(top_competitors_df["Points"].max())
                )
            }
        )

# ============================================================
# PAGE 2: COMPETITIONS
# ============================================================
elif page == NAV_COMPETITIONS:
    st.markdown(
        """
        <div class="main-header">
            <div class="main-title">Competition Analytics</div>
            <div class="main-subtitle">Explore tennis competitions, categories, formats, and hierarchy.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    t_comp = len(competitions_df)
    t_cat = len(categories_df)
    t_dbl = len(competitions_df[competitions_df["competition_name"].str.lower().str.contains("doubles", na=False)])
    t_par = len(competitions_df[competitions_df["parent_id"].isna()])

    col1, col2, col3, col4 = st.columns(4)
    with col1: display_kpi("Total Competitions", f"{t_comp:,}")
    with col2: display_kpi("Categories", f"{t_cat:,}")
    with col3: display_kpi("Doubles Events", f"{t_dbl:,}")
    with col4: display_kpi("Top-Level Events", f"{t_par:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "📋 All Competitions",
            "📊 By Category",
            "🎾 Doubles",
            "🔎 Category Search",
            "🔗 Parent / Sub",
            "📈 Type Distribution",
            "🏆 Top-Level"
        ]
    )

    merged_comp_df = competitions_df.merge(categories_df, on="category_id", how="left")

    with tab1:
        st.markdown('<div class="section-header">📋 All Competitions with Category</div>', unsafe_allow_html=True)
        all_comp_df = merged_comp_df[["competition_id", "competition_name", "type", "gender", "category_name"]] \
            .sort_values(by="competition_name")

        if not all_comp_df.empty:
            search = st.text_input("🔍 Search competition", placeholder="Enter competition Name...", key="tab1_search")
            filtered_df = all_comp_df[all_comp_df["competition_name"].str.contains(search, case=False, na=False)] if search else all_comp_df
            st.caption(f"Showing {len(filtered_df):,} of {len(all_comp_df):,} competitions")
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown('<div class="section-header">📊 Competitions per Category</div>', unsafe_allow_html=True)
        cat_comp_df = categories_df.merge(competitions_df, on="category_id", how="left") \
            .groupby(["category_id", "category_name"], as_index=False) \
            .agg(total_competitions=("competition_id", "count")) \
            .sort_values(by="total_competitions", ascending=False)

        if not cat_comp_df.empty:
            fig = px.bar(
                cat_comp_df.head(15),
                x="total_competitions",
                y="category_name",
                orientation="h",
                text_auto=True,
                color="total_competitions",
                color_continuous_scale="Blues",
                labels={"total_competitions": "Competitions", "category_name": "Category"}
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(yaxis=dict(autorange="reversed"))
            apply_chart_theme(fig, height=500)
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown('<div class="section-header">🎾 Doubles Competitions</div>', unsafe_allow_html=True)
        doubles_df = merged_comp_df[merged_comp_df["competition_name"].str.lower().str.contains("doubles", na=False)] \
            [["competition_id", "competition_name", "type", "gender", "category_name"]] \
            .sort_values(by="competition_name")

        if not doubles_df.empty:
            st.metric("Doubles Competitions Found", f"{len(doubles_df):,}")
            st.dataframe(doubles_df, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown('<div class="section-header">🔎 Competitions by Selected Category</div>', unsafe_allow_html=True)
        category_names = sorted(categories_df["category_name"].dropna().unique().tolist())
        if category_names:
            default_idx = category_names.index("ITF Men") if "ITF Men" in category_names else 0
            selected_category = st.selectbox("Select a category", category_names, index=default_idx)
            
            sel_cat_df = merged_comp_df[merged_comp_df["category_name"] == selected_category] \
                [["competition_id", "competition_name", "type", "gender", "category_name"]] \
                .sort_values(by="competition_name")
            st.dataframe(sel_cat_df, use_container_width=True, hide_index=True)

    with tab5:
        st.markdown('<div class="section-header">🔗 Parent and Sub-Competitions</div>', unsafe_allow_html=True)
        hierarchy_df = competitions_df[competitions_df["parent_id"].notna()].merge(
            competitions_df, left_on="parent_id", right_on="competition_id", suffixes=("", "_parent")
        )
        hierarchy_df = hierarchy_df.rename(columns={
            "competition_name": "sub_competition",
            "competition_name_parent": "parent_competition"
        })[["competition_id", "sub_competition", "parent_competition", "type", "gender"]] \
          .sort_values(by=["parent_competition", "sub_competition"])

        if not hierarchy_df.empty:
            st.dataframe(hierarchy_df, use_container_width=True, hide_index=True)

    with tab6:
        st.markdown('<div class="section-header">📈 Competition Type Distribution by Category</div>', unsafe_allow_html=True)
        type_dist_df = merged_comp_df.groupby(["category_name", "type"], as_index=False) \
            .agg(total_competitions=("competition_id", "count")) \
            .sort_values(by=["category_name", "total_competitions"], ascending=[True, False])

        if not type_dist_df.empty:
            category_filter = st.multiselect("Filter categories", sorted(type_dist_df["category_name"].dropna().unique()), default=[])
            if category_filter:
                chart_df = type_dist_df[type_dist_df["category_name"].isin(category_filter)]
            else:
                top_cats = type_dist_df.groupby("category_name")["total_competitions"].sum().nlargest(10).index
                chart_df = type_dist_df[type_dist_df["category_name"].isin(top_cats)]

            fig = px.bar(
                chart_df,
                x="category_name",
                y="total_competitions",
                color="type",
                barmode="stack",
                labels={"category_name": "Category", "total_competitions": "Competitions", "type": "Type"}
            )
            apply_chart_theme(fig, height=480)
            st.plotly_chart(fig, use_container_width=True)

    with tab7:
        st.markdown('<div class="section-header">🏆 Top-Level Competitions</div>', unsafe_allow_html=True)
        top_level_df = merged_comp_df[merged_comp_df["parent_id"].isna()] \
            [["competition_id", "competition_name", "type", "gender", "category_name"]] \
            .sort_values(by="competition_name")

        if not top_level_df.empty:
            st.dataframe(top_level_df, use_container_width=True, hide_index=True)


# ============================================================
# PAGE 3: VENUES & LOGISTICS
# ============================================================
elif page == NAV_VENUES:
    st.markdown(
        """
        <div class="main-header">
            <div class="main-title">Venues & Geographical Logistics</div>
            <div class="main-subtitle">Explore tennis venues, sports complexes, geographical distribution and timezones.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    t_c = len(complexes_df)
    t_v = len(venues_df)
    t_cntry = venues_df["country_name"].nunique()
    t_tz = venues_df["timezone"].nunique()

    col1, col2, col3, col4 = st.columns(4)
    with col1: display_kpi("Complexes", f"{t_c:,}")
    with col2: display_kpi("Venues", f"{t_v:,}")
    with col3: display_kpi("Countries", f"{t_cntry:,}")
    with col4: display_kpi("Timezones", f"{t_tz:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "📋 All Venues",
            "📊 Venues per Complex",
            "🌎 Country Search",
            "🕐 Timezones",
            "🏟️ Multi-Venue Complexes",
            "🌍 By Country",
            "🔎 Complex Search"
        ]
    )

    merged_venues_df = venues_df.merge(complexes_df, on="complex_id", how="left")

    with tab1:
        st.markdown('<div class="section-header">📋 All Venues with Associated Complex</div>', unsafe_allow_html=True)
        venues_display_df = merged_venues_df[["venue_id", "venue_name", "city_name", "country_name", "country_code", "timezone", "complex_name"]] \
            .sort_values(by="venue_name")

        if not venues_display_df.empty:
            search_v = st.text_input("🔍 Search venue", placeholder="Enter venue Name...", key="v_search")
            filtered_v = venues_display_df[venues_display_df["venue_name"].str.contains(search_v, case=False, na=False)] if search_v else venues_display_df
            st.dataframe(filtered_v, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown('<div class="section-header">📊 Number of Venues in Each Complex</div>', unsafe_allow_html=True)
        v_per_c_df = complexes_df.merge(venues_df, on="complex_id", how="left") \
            .groupby(["complex_id", "complex_name"], as_index=False) \
            .agg(total_venues=("venue_id", "count")) \
            .sort_values(by="total_venues", ascending=False)

        if not v_per_c_df.empty:
            fig = px.bar(
                v_per_c_df.head(15),
                x="total_venues",
                y="complex_name",
                orientation="h",
                text_auto=True,
                color="total_venues",
                color_continuous_scale="Tealgrn"
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(yaxis=dict(autorange="reversed"))
            apply_chart_theme(fig, height=480)
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown('<div class="section-header">🌎 Venues in a Specific Country</div>', unsafe_allow_html=True)
        countries = sorted(venues_df["country_name"].dropna().unique().tolist())
        if countries:
            default_c = countries.index("Chile") if "Chile" in countries else 0
            selected_Country = st.selectbox("Select Country", countries, index=default_c)
            
            c_venues_df = merged_venues_df[merged_venues_df["country_name"] == selected_Country] \
                [["venue_id", "venue_name", "city_name", "country_name", "country_code", "timezone", "complex_name"]] \
                .sort_values(by="venue_name")
            st.dataframe(c_venues_df, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown('<div class="section-header">🕐 Venues and Their Timezones</div>', unsafe_allow_html=True)
        timezone_df = venues_df[["venue_name", "city_name", "country_name", "timezone"]] \
            .sort_values(by=["timezone", "venue_name"])

        if not timezone_df.empty:
            tz_filter = st.multiselect("Filter by timezone", sorted(timezone_df["timezone"].dropna().unique()))
            filtered_tz = timezone_df[timezone_df["timezone"].isin(tz_filter)] if tz_filter else timezone_df
            st.dataframe(filtered_tz, use_container_width=True, hide_index=True)

    with tab5:
        st.markdown('<div class="section-header">🏟️ Complexes with More Than One Venue</div>', unsafe_allow_html=True)
        multi_venue_df = complexes_df.merge(venues_df, on="complex_id", how="inner") \
            .groupby(["complex_id", "complex_name"], as_index=False) \
            .agg(total_venues=("venue_id", "count"))
        multi_venue_df = multi_venue_df[multi_venue_df["total_venues"] > 1].sort_values(by="total_venues", ascending=False)

        if not multi_venue_df.empty:
            fig = px.bar(
                multi_venue_df.head(15),
                x="total_venues",
                y="complex_name",
                orientation="h",
                text_auto=True,
                color="total_venues",
                color_continuous_scale="Blues"
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(yaxis=dict(autorange="reversed"))
            apply_chart_theme(fig, height=450)
            st.plotly_chart(fig, use_container_width=True)

    with tab6:
        st.markdown('<div class="section-header">🌍 Venues Grouped by Country</div>', unsafe_allow_html=True)
        c_group_df = venues_df.groupby(["country_name", "country_code"], as_index=False) \
            .agg(total_venues=("venue_id", "count")) \
            .sort_values(by="total_venues", ascending=False)

        if not c_group_df.empty:
            fig = px.bar(
                c_group_df.head(20),
                x="total_venues",
                y="country_name",
                orientation="h",
                text_auto=True,
                color="total_venues",
                color_continuous_scale="Viridis"
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(yaxis=dict(autorange="reversed"))
            apply_chart_theme(fig, height=500)
            st.plotly_chart(fig, use_container_width=True)

    with tab7:
        st.markdown('<div class="section-header">🔎 Venues for a Specific Complex</div>', unsafe_allow_html=True)
        complex_names = sorted(complexes_df["complex_name"].dropna().unique().tolist())
        if complex_names:
            default_cmplx = complex_names.index("Nacional") if "Nacional" in complex_names else 0
            selected_complex = st.selectbox("Select complex", complex_names, index=default_cmplx)
            
            sel_cmplx_df = merged_venues_df[merged_venues_df["complex_name"] == selected_complex] \
                [["venue_id", "venue_name", "city_name", "country_name", "country_code", "timezone", "complex_name"]] \
                .sort_values(by="venue_name")
            st.dataframe(sel_cmplx_df, use_container_width=True, hide_index=True)


# ============================================================
# PAGE 4: COMPETITOR RankINGS
# ============================================================
elif page == NAV_RankINGS:
    st.markdown(
        """
        <div class="main-header">
            <div class="main-title">Player Rankings & Performance</div>
            <div class="main-subtitle">Explore doubles Rankings, competitor performance, point distribution, and Country insights.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    t_comp = len(competitors_df)
    t_cntry = competitors_df["Country"].nunique()
    t_pts = int(Rankings_df["Points"].max())
    t_stbl = len(Rankings_df[Rankings_df["Movement"] == 0])
    t_top5 = len(Rankings_df[Rankings_df["Rank"] <= 5])

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: display_kpi("Competitors", f"{t_comp:,}")
    with col2: display_kpi("Countries", f"{t_cntry:,}")
    with col3: display_kpi("Highest Points", f"{t_pts:,}")
    with col4: display_kpi("Stable Ranks", f"{t_stbl:,}")
    with col5: display_kpi("Top 5 Players", f"{t_top5:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "📋 All Rankings",
            "🏆 Top 5",
            "↔️ Stable Rank",
            "🌍 Country Analysis",
            "📊 Competitors by Country",
            "⭐ Highest Points"
        ]
    )

    merged_Rankings_df = competitors_df.merge(Rankings_df, on="Competitor_id")

    with tab1:
        st.markdown('<div class="section-header">📋 Competitor Rankings Explorer</div>', unsafe_allow_html=True)
        all_Rankings_df = merged_Rankings_df[["Competitor_id", "Name", "Country", "Country_code", "Rank", "Movement", "Points", "Competitions_played"]] \
            .sort_values(by="Rank")

        if not all_Rankings_df.empty:
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1: search_Name = st.text_input("🔍 Search competitor", placeholder="Enter competitor Name...", key="Rank_s")
            with c_f2:
                countries = sorted(all_Rankings_df["Country"].dropna().unique().tolist())
                selected_countries = st.multiselect("🌍 Filter by Country", countries)
            with c_f3:
                max_Rank = int(all_Rankings_df["Rank"].max())
                Rank_range = st.slider("🏆 Rank range", min_value=1, max_value=max_Rank, value=(1, min(50, max_Rank)))

            min_Points = st.number_input("⭐ Minimum Ranking Points", min_value=0, max_value=int(all_Rankings_df["Points"].max()), value=0, step=100)

            filtered_df = all_Rankings_df.copy()
            if search_Name: filtered_df = filtered_df[filtered_df["Name"].str.contains(search_Name, case=False, na=False)]
            if selected_countries: filtered_df = filtered_df[filtered_df["Country"].isin(selected_countries)]
            filtered_df = filtered_df[(filtered_df["Rank"] >= Rank_range[0]) & (filtered_df["Rank"] <= Rank_range[1]) & (filtered_df["Points"] >= min_Points)]

            st.caption(f"Showing {len(filtered_df):,} of {len(all_Rankings_df):,} competitors")
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Points": st.column_config.ProgressColumn("Points", format="%d", min_value=0, max_value=int(all_Rankings_df["Points"].max())),
                    "Movement": st.column_config.NumberColumn("Movement", format="%+d")
                }
            )

    with tab2:
        st.markdown('<div class="section-header">🏆 Top 5 Competitors</div>', unsafe_allow_html=True)
        top_five_df = merged_Rankings_df[merged_Rankings_df["Rank"] <= 5] \
            [["Competitor_id", "Name", "Country", "Rank", "Movement", "Points", "Competitions_played"]] \
            .sort_values(by="Rank")

        if not top_five_df.empty:
            st.dataframe(top_five_df, use_container_width=True, hide_index=True)
            fig = px.bar(
                top_five_df,
                x="Name",
                y="Points",
                text_auto=True,
                color="Points",
                color_continuous_scale="Blues",
                labels={"Name": "Competitor", "Points": "Ranking Points"},
                hover_data=["Country", "Rank", "Movement"]
            )
            fig.update_coloraxes(showscale=False)
            apply_chart_theme(fig, height=400)
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown('<div class="section-header">↔️ Competitors with No Rank Movement</div>', unsafe_allow_html=True)
        stable_df = merged_Rankings_df[merged_Rankings_df["Movement"] == 0] \
            [["Competitor_id", "Name", "Country", "Rank", "Movement", "Points", "Competitions_played"]] \
            .sort_values(by="Rank")

        if not stable_df.empty:
            search_stable = st.text_input("🔍 Search stable competitor", placeholder="Enter competitor Name...", key="stable_search")
            display_stable_df = stable_df[stable_df["Name"].str.contains(search_stable, case=False, na=False)] if search_stable else stable_df
            st.dataframe(display_stable_df, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown('<div class="section-header">🌍 Country-Wise Ranking Points</div>', unsafe_allow_html=True)
        countries = sorted(competitors_df["Country"].dropna().unique().tolist())
        if countries:
            default_cntry = countries.index("Croatia") if "Croatia" in countries else 0
            selected_Country = st.selectbox("Select Country", countries, index=default_cntry, key="c_pts_select")
            
            Country_competitors_df = merged_Rankings_df[merged_Rankings_df["Country"] == selected_Country] \
                [["Name", "Country", "Rank", "Movement", "Points", "Competitions_played"]] \
                .sort_values(by="Rank")

            if not Country_competitors_df.empty:
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1: display_kpi("Competitors", f"{len(Country_competitors_df):,}")
                with col_c2: display_kpi("Total Points", f"{int(Country_competitors_df['Points'].sum()):,}")
                with col_c3: display_kpi("Average Points", f"{Country_competitors_df['Points'].mean():,.0f}")
                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(Country_competitors_df, use_container_width=True, hide_index=True)

    with tab5:
        st.markdown('<div class="section-header">📊 Competitors by Country</div>', unsafe_allow_html=True)
        competitors_Country_df = competitors_df.groupby("Country", as_index=False) \
            .agg(total_competitors=("Competitor_id", "count")) \
            .sort_values(by="total_competitors", ascending=False)

        if not competitors_Country_df.empty:
            fig = px.bar(
                competitors_Country_df.head(20),
                x="total_competitors",
                y="Country",
                orientation="h",
                text_auto=True,
                color="total_competitors",
                color_continuous_scale="Viridis"
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(yaxis=dict(autorange="reversed"))
            apply_chart_theme(fig, height=500)
            st.plotly_chart(fig, use_container_width=True)

    with tab6:
        st.markdown('<div class="section-header">⭐ Highest Ranking Points</div>', unsafe_allow_html=True)
        max_Points = int(Rankings_df["Points"].max())
        highest_competitors_df = merged_Rankings_df[merged_Rankings_df["Points"] == max_Points] \
            [["Competitor_id", "Name", "Country", "Rank", "Movement", "Points", "Competitions_played"]] \
            .sort_values(by="Rank")

        st.metric("Highest Ranking Points Standard", f"{max_Points:,}")
        st.dataframe(highest_competitors_df, use_container_width=True, hide_index=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #94A3B8; font-size: 13px; padding-bottom: 20px;">
        Tennis Game Analytics Studio • Powered by Streamlit & Plotly
    </div>
    """,
    unsafe_allow_html=True
)
