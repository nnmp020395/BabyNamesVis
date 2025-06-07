import streamlit as st
import pandas as pd
import altair as alt
import unicodedata
from utils.preprocessing import load_and_clean_data

# On supprime accents et met en minuscule
def normalize_prenom(name):
    return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()

st.title("Évolution de la popularité des prénoms en France")

# Chargement des données et prétraitement
df = load_and_clean_data("data/dpt2020.csv")
df['annais'] = df['annais'].astype(int)

# Curseur
year_slider = alt.binding_range(
    min=df['annais'].min(),
    max=df['annais'].max(),
    step=1,
    name='Année : '
)

year_select = alt.param(
    name='year_param',
    bind=year_slider,
    value=df['annais'].min()
)

# Nom personnalisé
raw_input = st.text_input("Suivre un prénom :", value="", placeholder="ex: Emma")
prenom_cible = normalize_prenom(raw_input.strip())

# Si un prénom est renseigné, construire le graphique dynamique autour
if prenom_cible:
    # Somme par année + prénom
    df_grouped = (
        df.groupby(['annais', 'preusuel'], as_index=False)['nombre']
        .sum()
    )
    df_grouped['preusuel_normalized'] = df_grouped['preusuel'].apply(normalize_prenom)

    # Rang
    df_grouped['rang'] = (
        df_grouped.groupby('annais')['nombre']
        .rank(method='first', ascending=False)
        .astype(int)
    )

    # Mise en évidence du prénom cible
    df_grouped['is_target'] = df_grouped['preusuel_normalized'] == prenom_cible

    def extract_window(group):
        if prenom_cible in group['preusuel_normalized'].values:
            rang_cible = group[group['preusuel_normalized'] == prenom_cible]['rang'].values[0]
            return group[(group['rang'] >= rang_cible - 4) & (group['rang'] <= rang_cible + 5)]
        return pd.DataFrame()

    df_window = df_grouped.groupby('annais', group_keys=False).apply(extract_window).reset_index(drop=True)

    df_window['rang_label'] = df_window['rang'].astype(str) + '. ' + df_window['preusuel']

    # Graphique dynamique via Altair
    chart = (
        alt.Chart(df_window)
        .mark_bar()
        .encode(
            x=alt.X('nombre:Q', title='Nombre de naissances'),
            y=alt.Y('rang_label:N', sort='-x', title='Prénom'),
            color=alt.condition(
                'datum.is_target',
                alt.value('crimson'),
                alt.value('steelblue')
            ),
            tooltip=['rang', 'preusuel', 'nombre']
        )
        .add_params(year_select)
        .transform_filter(alt.datum.annais == year_select)
        .properties(
            title=f"Classement autour de {raw_input.strip().capitalize()}",
            height=400
        )
    )

    st.altair_chart(chart, use_container_width=True)

else:
    # Si aucun prénom, afficher le Top 10 standard
    top_per_year = (
        df.groupby(['annais', 'preusuel'])['nombre']
        .sum()
        .reset_index()
    )

    top_per_year = (
        top_per_year.groupby('annais', group_keys=False, observed=True)
        .apply(lambda x: x.nlargest(10, 'nombre'))
        .reset_index(drop=True)
    )

    top_per_year['rang'] = (
        top_per_year.groupby('annais')['nombre']
        .rank(method='first', ascending=False)
        .astype(int)
    )

    top_per_year['rang_label'] = top_per_year['rang'].astype(str) + '. ' + top_per_year['preusuel']

    chart = (
        alt.Chart(top_per_year)
        .mark_bar()
        .encode(
            x=alt.X('nombre:Q', title='Nombre de naissances'),
            y=alt.Y('rang_label:N', sort='-x', title='Top 10 prénoms'),
            tooltip=['rang', 'preusuel', 'nombre'],
            color=alt.Color('preusuel:N', legend=None)
        )
        .add_params(year_select)
        .transform_filter(alt.datum.annais == year_select)
        .properties(height=400)
    )

    st.altair_chart(chart, use_container_width=True)
