import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))                    
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))       
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

from utils.viz_utils import (
    get_top_names_by_region_viz,
    get_region_shapes,
    generate_wordcloud,
    create_mask_from_shape,
    render_choropleth_matplotlib,
)

st.set_page_config(layout="wide", page_title="Baby Names France", page_icon="🗺️")
st.title("🗺️ Baby Names by Region in France")

geojson_path = os.path.join(project_root, "data", "processed", "regions.geojson")
csv_path = os.path.join(project_root, "data", "processed", "names_by_region.csv.gz")
csv_proportions_path = os.path.join(project_root, "data", "processed", "names_by_regions_proportion.csv.gz")


@st.cache_data
def load_data():
    """Load all required datasets."""
    compression = 'gzip' if csv_path.endswith('.gz') else None
    df = pd.read_csv(csv_path, compression=compression)

    compression_prop = 'gzip' if csv_proportions_path.endswith('.gz') else None
    df_proportions = pd.read_csv(csv_proportions_path, compression=compression_prop)

    regions_gdf = gpd.read_file(geojson_path)
    return df, df_proportions, regions_gdf

@st.cache_data
def render_wordcloud_map(df_filtered_years, geojson_path, _regions_gdf):
    """Render wordcloud map for a given time range."""
    region_shapes = get_region_shapes(geojson_path)
    top_names = get_top_names_by_region_viz(df_filtered_years, top_n=50)

    minx, miny, maxx, maxy = _regions_gdf.total_bounds
    fig, ax = plt.subplots(figsize=(10, 12))
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_aspect('equal')

    pastel_colors = [
        "#f9f8fc", "#f4fae9", "#fef5f6", "#edf9d4",
        "#fef2e8", "#f1f6fb", "#fee8d1", "#e9eaf7",
        "#f3fbf3", "#fcfdea", "#fdeff1", "#ecf8f6",
        "#fff8eb", "#ecf8eb", "#f7fcf5", "#fbf9fc"
    ]

    for idx, (region_name, geom) in enumerate(region_shapes.items()):
        _regions_gdf[_regions_gdf["region_name"] == region_name].plot(
            ax=ax,
            facecolor=pastel_colors[idx % len(pastel_colors)],
            edgecolor="black",
            linewidth=1.5
        )

    for region_name, geom in region_shapes.items():
        region_df = top_names[top_names["region_name"] == region_name]
        freq_dict = dict(zip(region_df["preusuel"], region_df["nombre"]))
        if not freq_dict:
            continue

        mask, bounds = create_mask_from_shape(geom, resolution=800)
        wc = generate_wordcloud(
            name_freq_dict=freq_dict,
            mask_shape=mask,
            background_color=None,
            colormap="Dark2",
            mode="RGBA"
        )
        wc_img = wc.to_array()

        ax.imshow(
            wc_img,
            extent=[bounds[0], bounds[2], bounds[1], bounds[3]],
            interpolation="bilinear",
            zorder=10,
            aspect="auto"
        )

    ax.set_title(f"Top 50 Names by Region ({start_year} - {end_year})", fontsize=18)
    ax.axis("off")
    plt.tight_layout()
    return fig

try:
    df, df_proportions, regions_gdf = load_data()
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

years = sorted(df['annais'].dropna().unique())
years = [int(y) for y in years if str(y).isdigit()]

st.markdown("## 📅 Time Period Selection")
start_year, end_year = st.slider(
    "Select a year range:",
    min_value=min(years),
    max_value=max(years),
    value=(2000, 2020),
    step=1,
    help="Choose the time period for analysis"
)

df_filtered = df[df['annais'].astype(int).between(start_year, end_year)]
df_proportions_filtered = df_proportions[df_proportions['annais'].astype(int).between(start_year, end_year)]

wordcloud_fig = render_wordcloud_map(df_filtered, geojson_path, regions_gdf)

st.markdown("## 🌍 Regional Analysis")
st.markdown("### WordCloud Map by Region")
st.pyplot(wordcloud_fig)

st.markdown("---")

col1, col2 = st.columns([6, 4])

with col1:
    st.markdown("## 👶 Choropleth Map by Name")

    all_names = sorted(df_proportions_filtered['preusuel'].unique())

    if all_names:
        selected_name = st.selectbox(
            "Choose a name to visualize:",
            options=all_names,
            index=0,
            help="Type the first letters to filter (e.g., 'RO' for ROMAIN, ROBIN, ROBERT...)",
            placeholder="Type to search for a name..."
        )
        name_data = df_proportions_filtered[df_proportions_filtered['preusuel'] == selected_name]

        if not name_data.empty:
            with st.spinner(f"Generating choropleth map for {selected_name}..."):
                choropleth_fig = render_choropleth_matplotlib(
                    df_with_proportions=df_proportions_filtered,
                    regions_geojson_path=geojson_path,
                    selected_name=selected_name,
                    start_year=start_year,
                    end_year=end_year
                )
                st.pyplot(choropleth_fig, use_container_width=False)
                plt.close(choropleth_fig)

            metropolitan_regions = [
                'Auvergne-Rhône-Alpes', 'Bourgogne-Franche-Comté', 'Bretagne', 
                'Centre-Val de Loire', 'Corse', 'Grand Est', 'Hauts-de-France', 
                'Normandie', 'Nouvelle-Aquitaine', 'Occitanie', 'Pays de la Loire', 
                "Provence-Alpes-Côte d'Azur", 'Île-de-France'
            ]

            name_data_metro = name_data[name_data['region_name'].isin(metropolitan_regions)]

            top_regions_metro = (
                name_data_metro.groupby('region_name')['proportion_birth']
                .mean()
                .sort_values(ascending=False)
                .head(3)
            )

            st.markdown("**Top 3 most popular regions:**")
            for i, (region, proportion) in enumerate(top_regions_metro.items(), 1):
                st.write(f"{i}. {region} ({proportion:.2f}%)")
            
            st.markdown("*Note: For readability reasons, Corsica is not colored on the map.*")

            total_births = name_data['nombre'].sum()
            total_births_by_name = (
                df_proportions_filtered.groupby('preusuel')['nombre']
                .sum()
                .sort_values(ascending=False)
            )
            name_rank = total_births_by_name.index.get_loc(selected_name) + 1
            total_names = len(total_births_by_name)

            col1_stats, col2_stats = st.columns(2)
            col1_stats.markdown(f"""
            <div style='text-align: center;'>
            <div style='font-size: 14px;'>Total Births</div>
            <div style='font-size: 32px; font-weight: bold;'>{total_births:,}</div>
            </div>
            """, unsafe_allow_html=True)

            col2_stats.markdown(f"""
            <div style='text-align: center;'>
            <div style='font-size: 14px;'>Rank</div>
            <div style='font-size: 32px; font-weight: bold;'>#{name_rank} / {total_names}</div>
            </div>
            """, unsafe_allow_html=True)

with col2:
    st.markdown("### 📍 Regional Details")
    regions = sorted(df['region_name'].dropna().unique())
    selected_region = st.selectbox("Select a region:", options=regions)

    @st.cache_data
    def render_top_names_bar_chart(df_filtered, region, start_year, end_year):
        """Render bar chart with gender-specific colors."""
        df_region = df_filtered[df_filtered["region_name"] == region]
        if df_region.empty:
            return None

        top_names = (
            df_region.groupby(["preusuel", "sexe"])["nombre"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        color_map = {1: "darkblue", 2: "steelblue"}
        colors = top_names["sexe"].map(color_map)

        fig, ax = plt.subplots(figsize=(10, 8))
        bars = ax.barh(top_names["preusuel"], top_names["nombre"], color=colors)
        ax.invert_yaxis()
        ax.set_title(f"Top 10 Names in {region}\n({start_year} - {end_year})", fontsize=12)
        ax.set_xlabel("Number of Births")

        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height() / 2, f'{int(width):,}',
                    ha='left', va='center', fontsize=9)

        plt.tight_layout()
        return fig

    bar_chart_fig = render_top_names_bar_chart(df_filtered, selected_region, start_year, end_year)
    if bar_chart_fig:
        st.pyplot(bar_chart_fig, use_container_width=True)

st.markdown("---")
st.markdown("### 📊 About this visualization")
st.markdown("""
This interactive dashboard explores baby name trends across French regions using:
- **WordCloud Map**: Shows the most popular names in each region
- **Regional Analysis**: Detailed view of top names per region
- **Choropleth Map**: Geographic distribution of individual names

Data covers French baby names by department and year, aggregated by region.
""")