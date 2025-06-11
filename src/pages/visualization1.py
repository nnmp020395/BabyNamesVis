import streamlit as st
import pandas as pd
import altair as alt
import unicodedata
from pathlib import Path
from utils.preprocessing import load_and_clean_data

st.set_page_config(layout="wide")



# Get path to project root (one level up from src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Now construct the path to the data file
DATA_FILE = PROJECT_ROOT / "data" / "dpt2020.csv"
INFO_FILE = PROJECT_ROOT / "data" / "yearly_info.csv"


def normalize_prenom(name):
    return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()

st.title("Évolution de la popularité des prénoms en France")

# Chargement des données
df = load_and_clean_data(DATA_FILE)
df['annais'] = df['annais'].astype(int)

info_df = pd.read_csv(INFO_FILE)
info_df['year'] = info_df['year'].astype(int)

# One unified slider for all components
min_year = df['annais'].min()
max_year = df['annais'].max()

selected_year = st.slider("Sélectionnez une année", min_value=min_year, max_value=max_year, value=1900, step=1)

# Nom cible
raw_input = st.text_input("Suivre un prénom :", value="", placeholder="ex: Emma")
prenom_cible = normalize_prenom(raw_input.strip())

show_last_10 = st.checkbox("Afficher les 10 derniers prénoms du classement")

if prenom_cible:
    df_grouped = df.groupby(['annais', 'preusuel'], as_index=False)['nombre'].sum()
    df_grouped['preusuel_normalized'] = df_grouped['preusuel'].apply(normalize_prenom)

    df_grouped['rang'] = (
        df_grouped.groupby('annais')['nombre']
        .rank(method='first', ascending=False)
        .astype(int)
    )

    df_grouped['is_target'] = df_grouped['preusuel_normalized'] == prenom_cible
    df_target = df_grouped[df_grouped['preusuel_normalized'] == prenom_cible]

    def extract_window(group):
        if prenom_cible in group['preusuel_normalized'].values:
            rang_cible = group[group['preusuel_normalized'] == prenom_cible]['rang'].values[0]
            return group[(group['rang'] >= rang_cible - 4) & (group['rang'] <= rang_cible + 5)]
        return pd.DataFrame()

    df_window = df_grouped.groupby('annais', group_keys=False).apply(extract_window).reset_index(drop=True)
    df_window['rang_label'] = df_window['rang'].astype(str) + '. ' + df_window['preusuel']

    chart = (
        alt.Chart(df_window)
        .mark_bar()
        .encode(
            x=alt.X('nombre:Q', title='Nombre de naissances'),
            y=alt.Y('rang_label:N', sort='-x', title='Prénom'),
            color=alt.condition('datum.is_target', alt.value('crimson'), alt.value('steelblue')),
            tooltip=['rang', 'preusuel', 'nombre']
        )
        .transform_filter(alt.datum.annais == selected_year)
        .properties(
            title=f"Classement autour de {raw_input.strip().capitalize()} en {selected_year}",
            height=400
        )
    )
    st.altair_chart(chart, use_container_width=True)

    line_rank = alt.Chart(df_target).mark_line(color='orange').encode(
        x='annais:O',
        y=alt.Y('rang:Q', scale=alt.Scale(reverse=True)),
        tooltip=['annais', 'rang']
    )

    line_births = alt.Chart(df_target).mark_line(color='teal').encode(
        x='annais:O',
        y='nombre:Q',
        tooltip=['annais', 'nombre']
    )

    vertical_line = alt.Chart(df_target).mark_rule(color='red', strokeDash=[5, 5]).encode(
        x='annais:O'
    ).transform_filter(
        alt.datum.annais == selected_year
    )

    combined_chart = alt.layer(
        line_rank, line_births, vertical_line
    ).resolve_scale(
        y='independent'
    ).properties(
        title=f"Évolution du rang et du nombre de naissances pour {raw_input.strip().capitalize()}",
        height=400,
        width=800
    ).interactive()

    st.altair_chart(combined_chart)

else:
    top_per_year = (
        df.groupby(['annais', 'preusuel'])['nombre']
        .sum()
        .reset_index()
    )

    if show_last_10:
        top_per_year = (
            top_per_year.groupby('annais', group_keys=False, observed=True)
            .apply(lambda x: x.nsmallest(10, 'nombre'))
            .reset_index(drop=True)
        )
        chart_title = "Classement des prénoms les MOINS populaires"
    else:
        top_per_year = (
            top_per_year.groupby('annais', group_keys=False, observed=True)
            .apply(lambda x: x.nlargest(10, 'nombre'))
            .reset_index(drop=True)
        )
        chart_title = "Classement des prénoms les PLUS populaires"

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
            y=alt.Y('rang_label:N', sort='-x', title=chart_title),
            tooltip=['rang', 'preusuel', 'nombre'],
            color=alt.Color('preusuel:N', legend=None)
        )
        .transform_filter(alt.datum.annais == selected_year)
        .properties(height=400)
    )

    st.altair_chart(chart, use_container_width=True)

# Info panel (uses the same selected_year)
info_row = info_df[info_df['year'] == selected_year]

if not info_row.empty:
    st.sidebar.markdown("### ℹ️ Contexte historique")
    st.sidebar.info(info_row.iloc[0]['info'])
else:
    st.sidebar.info("Pas d'information disponible pour cette année.")
