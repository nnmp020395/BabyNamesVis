import streamlit as st
import pandas as pd
import altair as alt
from utils.preprocessing import load_and_clean_data

st.title("Évolution des prénoms les plus donnés par année (Top 10)")

# 1. Chargement et nettoyage
df = load_and_clean_data("data/dpt2020.csv")
df['annais'] = df['annais'].astype(int)

# 2. Top 10 prénoms par année
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

# 3. Curseur interactif
year_slider = alt.binding_range(
    min=top_per_year['annais'].min(),
    max=top_per_year['annais'].max(),
    step=1,
    name='Année : '
)

year_select = alt.param(
    name='year_param',
    bind=year_slider,
    value=top_per_year['annais'].min()
)

# 4. Bar chart dynamique
chart = (
    alt.Chart(top_per_year)
    .mark_bar()
    .encode(
        x=alt.X('nombre:Q', title='Nombre de naissances'),
        y=alt.Y('preusuel:N', sort='-x', title='Prénom'),
        tooltip=['preusuel', 'nombre'],
        color=alt.Color('preusuel:N', legend=None)
    )
    .add_params(year_select)
    .transform_filter(alt.datum.annais == year_select)
    .properties(height=400)
)

st.altair_chart(chart, use_container_width=True)
