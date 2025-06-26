import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
import geopandas as gpd
from wordcloud import WordCloud
import numpy as np
import pandas as pd
from shapely.geometry import mapping
from rasterio import features
import altair as alt
import json

def generate_wordcloud(name_freq_dict, mask_shape=None, background_color=None, colormap='tab20', mode='RGBA'):
    """
    Generate a word cloud from a dictionary of name frequencies.

    Parameters:
    - name_freq_dict (dict): Dictionary of names and their frequencies.
    - mask_shape (np.ndarray): Optional mask for shaping the word cloud.
    - background_color (str): Background color for the word cloud.
    - colormap (str): Color map to use.
    - mode (str): Rendering mode, usually 'RGB' or 'RGBA'.

    Returns:
    - WordCloud object.
    """
    wc = WordCloud(
        width=mask_shape.shape[1] if mask_shape is not None else 400,
        height=mask_shape.shape[0] if mask_shape is not None else 400,
        background_color=background_color,
        colormap=colormap,
        mask=mask_shape,
        mode=mode,
        contour_width=0
    )
    return wc.generate_from_frequencies(name_freq_dict)

def get_region_shapes(geojson_path):
    """
    Load region shapes from a GeoJSON file.

    Parameters:
    - geojson_path (str): Path to the GeoJSON file.

    Returns:
    - dict: Mapping from region names to Shapely geometries.
    """
    regions = gpd.read_file(geojson_path)
    shapes = {
        row['region_name']: row['geometry']
        for idx, row in regions.iterrows()
    }
    return shapes

def get_top_names_by_region_viz(df, top_n=50):
    """
    Return the top N names by frequency for each region.

    Parameters:
    - df (pd.DataFrame): DataFrame containing region_name, preusuel, and nombre.
    - top_n (int): Number of top names to select per region.

    Returns:
    - pd.DataFrame: Filtered DataFrame with top names.
    """
    grouped = (
        df.groupby(['region_name', 'preusuel'])['nombre']
        .sum()
        .reset_index()
    )
    top_names = (
        grouped.sort_values(['region_name', 'nombre'], ascending=[True, False])
        .groupby('region_name')
        .head(top_n)
    )
    return top_names

def create_mask_from_shape(shape, resolution=800):
    """
    Create a binary mask from a given Shapely shape.

    Parameters:
    - shape (shapely.geometry): The region shape.
    - resolution (int): Width resolution of the mask.

    Returns:
    - mask (np.ndarray): Binary mask.
    - bounds (tuple): Bounds of the shape.
    """
    bounds = shape.bounds
    width = resolution
    height = int((bounds[3] - bounds[1]) / (bounds[2] - bounds[0]) * resolution)

    transform = [
        (bounds[2] - bounds[0]) / width, 0, bounds[0],
        0, -(bounds[3] - bounds[1]) / height, bounds[3]
    ]

    mask = features.rasterize(
        [(mapping(shape), 1)],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=True,
        dtype=np.uint8
    )

    mask = np.where(mask == 1, 0, 255).astype(np.uint8)
    return mask, bounds

def prepare_choropleth_data_matplotlib(df, selected_name, start_year, end_year):
    """
    Prepare data for choropleth map rendering using matplotlib.

    Parameters:
    - df (pd.DataFrame): DataFrame containing name data.
    - selected_name (str): Name to filter.
    - start_year (int): Start year.
    - end_year (int): End year.

    Returns:
    - pd.DataFrame: DataFrame with average proportion per region.
    """
    filtered_df = df[
        (df['preusuel'] == selected_name) & 
        (df['annais'] >= start_year) & 
        (df['annais'] <= end_year)
    ].copy()

    filtered_df = filtered_df.dropna(subset=['region_name'])

    metropolitan_regions = [
        'Auvergne-Rhône-Alpes', 'Bourgogne-Franche-Comté', 'Bretagne', 
        'Centre-Val de Loire', 'Corse', 'Grand Est', 'Hauts-de-France', 
        'Normandie', 'Nouvelle-Aquitaine', 'Occitanie', 'Pays de la Loire', 
        "Provence-Alpes-Côte d'Azur", 'Île-de-France'
    ]

    filtered_df = filtered_df[filtered_df['region_name'].isin(metropolitan_regions)]

    if filtered_df.empty:
        return pd.DataFrame({
            'region_name': metropolitan_regions,
            'avg_proportion': [0.0] * len(metropolitan_regions)
        })

    region_proportions = (
        filtered_df.groupby('region_name')['proportion_birth']
        .mean()
        .reset_index()
        .rename(columns={'proportion_birth': 'avg_proportion'})
    )

    complete_data = pd.DataFrame({'region_name': metropolitan_regions})
    region_proportions = complete_data.merge(
        region_proportions, 
        on='region_name', 
        how='left'
    ).fillna(0)

    return region_proportions

def render_choropleth_matplotlib(df_with_proportions, regions_geojson_path, selected_name, start_year, end_year):
    """
    Render a choropleth map using matplotlib and geopandas.

    Parameters:
    - df_with_proportions (pd.DataFrame): DataFrame containing all name data.
    - regions_geojson_path (str): Path to GeoJSON file.
    - selected_name (str): Selected name.
    - start_year (int): Start year.
    - end_year (int): End year.

    Returns:
    - matplotlib.figure.Figure: The rendered figure.
    """
    try:
        proportion_data = prepare_choropleth_data_matplotlib(df_with_proportions, selected_name, start_year, end_year)

        gdf = gpd.read_file(regions_geojson_path)
        gdf['region_name'] = gdf['region_name'].str.strip()
        proportion_data['region_name'] = proportion_data['region_name'].str.strip()

        gdf_merged = gdf.merge(proportion_data, on='region_name', how='left')
        gdf_merged['avg_proportion'] = gdf_merged['avg_proportion'].fillna(0)

        fig, ax = plt.subplots(figsize=(12, 10))

        
        gdf_no_corse = gdf_merged[gdf_merged['region_name'] != 'Corse']
        gdf_no_corse.plot(
            column='avg_proportion',
            cmap='Blues',
            linewidth=0.8,
            ax=ax,
            edgecolor='darkgray',  
            legend=False  
        )
        
        gdf_corse = gdf_merged[gdf_merged['region_name'] == 'Corse']
        if not gdf_corse.empty:
            gdf_corse.plot(
                ax=ax,
                color='lightgray',
                linewidth=0.8,
                edgecolor='darkgray'  
            )

        from matplotlib import cm
        from matplotlib.colors import Normalize
        
        vmin = gdf_no_corse['avg_proportion'].min()
        vmax = gdf_no_corse['avg_proportion'].max()
        
        if vmax == 0:
            vmax = 0.1
        
        norm = Normalize(vmin=vmin, vmax=vmax)
        sm = plt.cm.ScalarMappable(norm=norm, cmap='Blues')  
        sm.set_array([])
        
        cbar = fig.colorbar(sm, ax=ax, shrink=0.6, aspect=20, pad=0.1)
        cbar.set_label(f'Average proportion (%) of name "{selected_name}"', rotation=270, labelpad=20)

        region_offsets = {
            'Nouvelle-Aquitaine': (0, 0),    
            'Provence-Alpes-Côte d\'Azur': (0, 0),   
            'Auvergne-Rhône-Alpes': (0, 0),
            'Occitanie': (0, 0),
            'Île-de-France': (0, 0),
            'Grand Est': (0, 0),
            'Hauts-de-France': (0, 0),
            'Normandie': (0, 0),
            'Bretagne': (0, 0),                  
            'Pays de la Loire': (0, 0),
            'Centre-Val de Loire': (0, 0),
            'Bourgogne-Franche-Comté': (0, 0),
            'Corse': (0, 0)
        }

        for idx, row in gdf_merged.iterrows():
            region_name = row['region_name']
            
            label_point = row['geometry'].representative_point()
            
            offset_x, offset_y = region_offsets.get(region_name, (0, 0))
            final_x = label_point.x + offset_x
            final_y = label_point.y + offset_y
            
            if region_name == 'Provence-Alpes-Côte d\'Azur':
                text = 'Provence-Alpes-\nCôte d\'Azur'
            else:
                text = region_name
                
            ax.text(
                final_x, final_y,
                text,
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=9,
                fontweight='bold',
                color='darkblue',
                zorder=20,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7)
            )

        ax.set_title(
            f'Geographic distribution of name "{selected_name}"\nPeriod: {start_year} - {end_year}', 
            fontsize=16, 
            fontweight='bold',
            pad=20
        )

        ax.axis('off')
        plt.tight_layout()
        return fig

    except Exception as e:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f'Error while generating map:\n{str(e)}', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=12, 
                bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))
        ax.set_title(f'Choropleth map - {selected_name}', fontsize=14)
        ax.axis('off')
        return fig