"""
Preprocessing functions for the 3 visualizations
"""
import numpy as np
import pandas as pd
import altair as alt
alt.data_transformers.enable('json')
import matplotlib.pyplot as plt


###############################################################################
# Visualisation 1
###############################################################################

def remove_rare_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Supprime les lignes où le prénom est '_PRENOMS_RARES'.
    """
    return df[df['preusuel'] != '_PRENOMS_RARES']

def remove_invalid_years(df: pd.DataFrame) -> pd.DataFrame:
    """
    Supprime les lignes où l'année est 'XXXX'.
    """
    return df[df['annais'] != 'XXXX']

def convert_year_to_int(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convertit la colonne 'annais' en entier.
    """
    df['annais'] = df['annais'].astype(int)
    return df

def load_and_clean_data(csv_path: str) -> pd.DataFrame:
    """
    Charge un fichier CSV et applique le nettoyage :
    - Suppression des noms rares
    - Suppression des années invalides
    - Conversion des années en entier
    """
    df = pd.read_csv(csv_path, sep=';')
    df = remove_rare_names(df)
    df = remove_invalid_years(df)
    df = convert_year_to_int(df)
    return df


###############################################################################
# Visualisation 2
###############################################################################

import pandas as pd

def clean_and_enrich_baby_names(csv_path, mapping_path):
    """
    Load, clean, and enrich the raw baby names dataset with regional information.
    
    This function processes the French baby names dataset by cleaning invalid entries,
    standardizing department codes, and adding regional information through mapping.
    Special handling is implemented for Corsica (department code '20').

    Parameters:
        csv_path (str): Path to the raw baby names CSV file
        mapping_path (str): Path to the CSV mapping departments to regions

    Returns:
        pd.DataFrame: Cleaned and enriched DataFrame with region names added
    """
    
    # Load the raw dataset
    df = pd.read_csv(csv_path, sep=';')

    # Remove rows with missing or invalid values
    df = df.dropna()
    df = df[(df['annais'] != 'XXXX') & (df['dpt'] != 'XX')]

    # Remove rows with rare names (aggregated category)
    df = df[df.preusuel != '_PRENOMS_RARES'].copy()

    # Convert columns to appropriate data types
    df['annais'] = df['annais'].astype(int)
    df['sexe'] = df['sexe'].astype(int)
    df['nombre'] = df['nombre'].astype(int)
    df['dpt'] = df['dpt'].astype(str).str.zfill(2)

    # Load and format the department-to-region mapping
    mapping = pd.read_csv(mapping_path)
    mapping['num_dep'] = mapping['num_dep'].astype(str)
    
    # Handle special case: Corsica department code mapping
    # Dataset uses '20' for Corsica, but mapping uses '2A' and '2B'
    # Map both 2A and 2B to department code '20' for consistency
    corsica_mapping = mapping[mapping['num_dep'].isin(['2A', '2B'])].copy()
    if not corsica_mapping.empty:
        corsica_unified = pd.DataFrame({
            'num_dep': ['20'],
            'dep_name': ['Corse'],
            'region_name': ['Corse']
        })
        mapping = pd.concat([mapping[~mapping['num_dep'].isin(['2A', '2B'])], corsica_unified], 
                           ignore_index=True)
    
    # Ensure department codes in mapping are zero-padded
    mapping['num_dep'] = mapping['num_dep'].apply(lambda x: x.zfill(2) if x.isdigit() else x)

    # Merge regional information into the dataset
    df = df.merge(mapping[['num_dep', 'region_name']], left_on='dpt', right_on='num_dep', how='left')
    df = df.drop(columns=['num_dep'])

    return df


def get_top_names_by_region(df, top_n=50):
    """
    Get the top N most popular names for each region.
    
    Groups the dataset by region and name, aggregates birth counts,
    and returns the most popular names per region.

    Parameters:
        df (pd.DataFrame): DataFrame containing baby names data with region information
        top_n (int): Number of top names to return per region (default: 50)

    Returns:
        pd.DataFrame: DataFrame with top N names per region, sorted by popularity
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


def add_proportion_column(df):
    """
    Add a proportion column calculating the percentage of each name within its region-year.
    
    For each row, calculates what percentage this specific name represents
    of all births in the same region and year.

    Parameters:
        df (pd.DataFrame): DataFrame containing baby names data with columns:
                          ['sexe', 'preusuel', 'annais', 'dpt', 'nombre', 'region_name']

    Returns:
        pd.DataFrame: Original DataFrame with added 'proportion_birth' column (percentage)
    """
    
    # Calculate total births per region per year
    total_births = (
        df.groupby(['region_name', 'annais'])['nombre']
        .sum()
        .reset_index()
        .rename(columns={'nombre': 'total_births_region_year'})
    )
    
    # Merge total births back to original dataframe
    df_with_totals = df.merge(
        total_births, 
        on=['region_name', 'annais'], 
        how='left'
    )
    
    # Calculate proportion as percentage
    df_with_totals['proportion_birth'] = (
        df_with_totals['nombre'] / df_with_totals['total_births_region_year'] * 100
    )
    
    # Clean up temporary column
    df_with_totals = df_with_totals.drop(columns=['total_births_region_year'])
    
    return df_with_totals


def create_names_by_regions_proportion_csv(input_csv_path, output_csv_path):
    """
    Create an enhanced dataset with birth proportions from the regional names dataset.
    
    Loads the processed regional names dataset, adds proportion calculations,
    and saves the result to a new CSV file.

    Parameters:
        input_csv_path (str): Path to the input names_by_region.csv file
        output_csv_path (str): Path where to save the enhanced CSV with proportions

    Returns:
        pd.DataFrame: The processed DataFrame with proportion data
    """
    
    # Load the processed data
    df = pd.read_csv(input_csv_path)
    
    # Add proportion calculations
    df_with_proportions = add_proportion_column(df)
    
    # Save enhanced dataset
    df_with_proportions.to_csv(output_csv_path, index=False)
    
    print(f"Successfully created {output_csv_path} with {len(df_with_proportions):,} records")
    print(f"Proportion range: {df_with_proportions['proportion_birth'].min():.4f}% - {df_with_proportions['proportion_birth'].max():.4f}%")
    
    return df_with_proportions




###############################################################################
# Visualisation 3
###############################################################################

class Dataset:
    def __init__(self, df):
        self.df = df

    def get_data(self):
        return self.df

    def get_cleaned_data(self):
        df_cleaned = self.df[(self.df['annais'] != 'XXXX') & (self.df['dpt'] != 'XX')]
        df_cleaned = df_cleaned[df_cleaned['preusuel'] != '_PRENOMS_RARES']
        self.df = df_cleaned.copy()
        return self.df

    def get_years(self):
        self.df['annais'] = self.df['annais'].astype(str)
        years = self.df['annais'].unique()
        years_sorted = sorted(years, key=int)
        return years_sorted

    def get_departments(self):
        return self.df['dpt'].unique()

    def get_names(self, sexe=None):
        if sexe == 'B':
            return self.df[self.df['sexe'] == 1]['preusuel'].unique()
        elif sexe == 'G':
            return self.df[self.df['sexe'] != 1]['preusuel'].unique()
        else:
            return self.df['preusuel'].unique()

    def get_dataset_by_gender(self, sexe=None):
        if sexe == 'B':
            return self.df[self.df['sexe'] == 1]
        elif sexe == 'G':
            return self.df[self.df['sexe'] != 1]
        elif sexe == 'M':
            mixed_names = self.get_mixed_names()
            return self.df[self.df['preusuel'].isin(mixed_names)]
        else:
            return self.df.copy()

    def get_name_counts(self, sexe=None):
        return self.df.groupby('preusuel').size().reset_index(name='count')

    def get_top_names(self, n=10, sexe=None):
        if sexe == 'B':
            df_sexe = self.df[self.df['sexe'] == 1]
        elif sexe == 'G':
            df_sexe = self.df[self.df['sexe'] != 1]
        elif sexe == 'M':
            mixte_names = self.get_mixed_names()
            df_sexe = self.df[self.df['preusuel'].isin(mixte_names)]
        else:
            df_sexe = self.df

        top_names = df_sexe.groupby('preusuel').size().reset_index(name='count')
        top_names = top_names.sort_values(by='count', ascending=False).head(n)
        return top_names

    def get_mixed_names(self):
        boys_names = self.get_names(sexe='B')
        girls_names = self.get_names(sexe='G')
        mixed_names = np.intersect1d(boys_names, girls_names)
        return mixed_names

    def get_global_gender_counts(self, with_mixed=False):
        grouped_annais_sexe = self.df.groupby(['annais', 'sexe'])['nombre'].sum().reset_index()
        if with_mixed:
            mixed_names = self.get_mixed_names()
            df_mixte = self.df[self.df['preusuel'].isin(mixed_names)]
            mixte_grouped_annais = df_mixte.groupby(['annais'])['nombre'].sum().reset_index()
            mixte_grouped_annais['sexe'] = 3  # Ajouter une colonne pour indiquer que c'est mixte

            # Fusionner les deux DataFrames
            merged_df = pd.concat([grouped_annais_sexe, mixte_grouped_annais], ignore_index=True)
            pivot_cols = ['boys', 'girls', 'mixed']

        merged_df = grouped_annais_sexe.copy(ignore_index=True)
        pivot_cols = ['boys', 'girls']
        pivot_merged_df = merged_df.pivot(index='annais', columns='sexe', values='nombre')
        pivot_merged_df.columns = pivot_cols
        # print("pivot_merged_df \n", pivot_merged_df.head())
        return pivot_merged_df.reset_index()

    def convert_to_pct(self):
        # assurer que les colonnes sont bien annais, sexe, preuseul, nombre
        grouped_df = self.df.groupby(['annais', 'sexe'])['nombre'].sum().reset_index()
        total_per_annais = grouped_df.groupby('annais')['nombre'].transform('sum')
        grouped_df['pct'] = grouped_df['nombre']/total_per_annais * 100
        return grouped_df


def plot_stacked_area_chart(data, start_year, end_year, name_selected=None, gender_selected=None):
    titre = f"All mixed babies names from {start_year} to {end_year} (stacked area chart) "
    data = data[(data['annais'] >= start_year) & (data['annais'] <= end_year)]
    # data = data[data['preusuel'] == name_selected].copy()
    if name_selected:
        data = data[data['preusuel'] == name_selected].copy()
        titre = f"How the name {name_selected} evolves from {start_year} to {end_year} (stacked area chart)"

    data_grouped = data.groupby(['annais', 'sexe'])['nombre'].sum().reset_index()
    source = data_grouped.pivot(index='annais', columns='sexe', values='nombre')
    source.columns = ['boys', 'girls']
    source = source.reset_index()
    source = source.melt(id_vars="annais",
                       value_vars=["boys", "girls"],
                       var_name="gender",
                       value_name="value")

    print("source data to plot \n:", source.head())

    color_scale = alt.Scale(
        domain=['boys', 'girls'],
        range=["#eff70a", "#eca9cb"]  # bleu pour garçon, rose pour fille (par exemple)
        )

    chart = alt.Chart(source).transform_calculate(
        order="{'boys':0, 'girls':1}[datum.variable]"
    ).mark_area().encode(
        x=alt.X("annais:O", title="Years"),
        y=alt.Y("value:Q", stack="zero", title="number of babies"),
        color=alt.Color("gender", scale=color_scale, title="Gender"),
        order=alt.Order("order:O")
    ).properties(
        width=800,
        height=400,
        title=titre
    )

    return chart

def line_chart_mixed_names(data, start_year, end_year):
    titre = f"Evolution boys / girls / mixed from {start_year} to {end_year}"
    data = data[(data['annais'] >= start_year) & (data['annais'] <= end_year)].copy()
    print("data to plot mixed names \n", data.head())
    columns = data.columns.tolist()
    source = data.melt(id_vars="annais",
                        value_vars=columns.remove('annais'),
                        var_name="gender",
                        value_name="value")
    color_scale = alt.Scale(
        domain=['boys', 'girls', 'mixed'],
        range=["#eff70a", "#eca9cb", "#6aafe6"]
    )

    chart = alt.Chart(source).mark_line(point=True).encode(
        x=alt.X("annais:O", title="Years"),
        y=alt.Y("value:Q", title="number of babies"),
        color=alt.Color("gender:N", scale=color_scale, title="Gender"),
    ).properties(
        width=800,
        height=400,
        title=titre
    )
    return chart


def multi_line_tooltip_by_gender(data):
    mapping = {1: 'A-Boys', 2: 'B-Boys mixed names', 3: 'C-Girls', 4: 'D-Girls mixed names'}
    data['sexe_label'] = data['sexe'].map(mapping)

    # Encode line style as string (not list!)
    def dash_style(label):
        return 'solid' if 'mixed' in label else 'dashed'

    data['line_style'] = data['sexe_label'].apply(dash_style)


    color_scale = alt.Scale(
        domain=['boys', 'mixed boys', 'girls', 'mixed girls'],
        range=["#0af7db", "#eca9cb", "#038a7b", "#986780"]
    )

    # line = alt.Chart(data).mark_line(interpolate="basis").encode(
    #     x="annais:T",
    #     y=alt.Y("nombre:Q"),
    #     color=alt.Color("sexe_label:N", scale=color_scale, title="Sexe"),
    #     strokeDash=alt.StrokeDash("line_style:N", legend=None)
    # )

    area = alt.Chart(data).mark_area().encode(
        alt.X("annais:T").axis(format="%Y", domain=False, grid=True ),
        alt.Y("nombre:Q").stack("center").axis(None),
        alt.Color("sexe_label:N").scale(scheme="category20"),
        ).properties(
            width=900,
            height=500,
    )
    return area

def heatmap_line_percent(data_base, data):
    x = data_base['annais'].unique()
    y = np.arange(101)
    xx, yy = np.meshgrid(x, y, indexing='ij')  # indexing='ij' pour avoir x en lignes, y en colonnes
    # Créer un compteur croissant pour value
    value = np.array([np.arange(101)] * data_base['annais'].unique().shape[0])
    df = pd.DataFrame({
        'x': xx.flatten(),
        'y': yy.flatten(),
        'value': value.flatten()
    })

    # Création de la heatmap Altair
    heatmap_base = alt.Chart(df).mark_rect().encode(
        x=alt.X('x:T', title='Years').axis(format="%Y"),
        y=alt.Y('y:O',
                title='Pourcents',
                scale=alt.Scale(reverse=True),
                axis=alt.Axis(values=list(range(0, 101, 10))),
        ),
        color=alt.Color('value:Q', 
                        scale=alt.Scale(
                            scheme='greens'), 
                            #domain=[0, 50, 100],      
                            #range=['bleu', 'white', 'red']
                        #),
                        title='Pourcents (%)')
    ).properties(
        width=600,
        height=500,
        # title='Heatmap [100x100] - valeur de 0 à 100%'
    )

    rule_50 = alt.Chart(pd.DataFrame({'y': [50]})).mark_rule(color='black', strokeDash=[4,4]).encode(
        y=alt.Y('y:O').axis(None)
    )

    # superposer line sur le heatmap, choisir seulement la ligne des noms mixtes portés par une fille
    source = data[data['sexe'] == data['sexe'].unique()[-1]]
    line = alt.Chart(source).mark_line().encode(
        x=alt.X("annais:T", title="Years").axis(format="%Y"),
        y=alt.Y("pct:Q").axis(None),
        color=alt.Color("sexe:N",
                        title="Sexe",
                        scale=alt.Scale(domain=source['sexe'].unique(), range=["black"]),
                        legend=alt.Legend(title="Sexe",
                                labelExpr=f"datum.value == {source['sexe'].unique()} ? 'Girls' : ''")
                        )
    )
    chart = alt.layer(heatmap_base + rule_50 + line)
    return chart
