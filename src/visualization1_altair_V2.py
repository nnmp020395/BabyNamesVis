import streamlit as st
import pandas as pd
import altair as alt
import unicodedata
#import time
from utils.preprocessing import load_and_clean_data

st.set_page_config(layout="wide")

# On supprime accents et met en minuscule
def normalize_prenom(name):
    return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()

st.title("Évolution de la popularité des prénoms en France")

# Chargement des données et prétraitement
df = load_and_clean_data("/Users/fabreindira/babynames/BabyNamesVis/data/dpt2020.csv")
df['annais'] = df['annais'].astype(int)

info_df = pd.read_csv("yearly_info.csv")
info_df['year'] = info_df['year'].astype(int)


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

# # Manual year tracking: infer year from chart using the parameter's default
# selected_year = year_select.value  # This only works for initial load

# # Workaround: display a manual Streamlit slider ONLY to sync info text
# selected_year_text = st.slider(
#     "Année pour la note d'information",
#     min_value=df['annais'].min(),
#     max_value=df['annais'].max(),
#     value=selected_year,
#     step=1,
#     key="year_text_sync"
# )

# This slider is just to select the year for displaying text — not for filtering charts
selected_info_year = st.sidebar.slider(
    "Année pour afficher l'information",
    min_value=info_df['year'].min(),
    max_value=info_df['year'].max(),
    value=2000,
    step=1
)


# Nom personnalisé
raw_input = st.text_input("Suivre un prénom :", value="", placeholder="ex: Emma")
prenom_cible = normalize_prenom(raw_input.strip())

# Toggle button pour choisir entre 10 meilleurs ou 10 derniers
show_last_10 = st.checkbox("Afficher les 10 derniers prénoms du classement")

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
    #df_grouped['is_target'] = df_grouped['preusuel_normalized'] == prenom_cible

    df_target = df_grouped[df_grouped['preusuel_normalized'] == prenom_cible]

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

    # Create line chart for rank and number of births
    line_rank = alt.Chart(df_target).mark_line(color='orange').encode(
        x='annais:O',
        y=alt.Y('rang:Q', scale=alt.Scale(reverse=True)),
        #y='rang:Q', for rank with low values at the bottom
        tooltip=['annais', 'rang']
    )

    line_births = alt.Chart(df_target).mark_line(color='teal').encode(
        x='annais:O',
        y='nombre:Q',
        tooltip=['annais', 'nombre']
    )

    vertical_line = alt.Chart(df_target).mark_rule(
        color='red', strokeDash=[5, 5]
    ).encode(
        x='annais:O'
    ).transform_filter(
        alt.datum.annais == year_select
    )

    # Combine the line charts and vertical line
    combined_chart = alt.layer(
        line_rank, line_births, vertical_line
    ).add_params(
        year_select
    # ).transform_filter(
    #     alt.datum.annais == year_select
    ).resolve_scale(
        y='independent'
    ).properties(
        title=f"Évolution du rang et du nombre de naissances pour {raw_input.strip().capitalize()}",
        height=400,
        width=800
    ).interactive()

    st.altair_chart(combined_chart) #, use_container_width=True)

else:
    # Si aucun prénom, afficher le Top 10 standard
    top_per_year = (
        df.groupby(['annais', 'preusuel'])['nombre']
        .sum()
        .reset_index()
    )

    if show_last_10:
        # Display the last 10 names
        #TODO : changer titre + classement
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
        .add_params(year_select)
        .transform_filter(alt.datum.annais == year_select)
        .properties(height=400)
    )

    st.altair_chart(chart, use_container_width=True)

# Show the info
info_row = info_df[info_df['year'] == selected_info_year]

if not info_row.empty:
    st.sidebar.markdown("### ℹ️ Contexte historique")
    st.sidebar.info(info_row.iloc[0]['info'])
else:
    st.sidebar.info("Pas d'information disponible pour cette année.")