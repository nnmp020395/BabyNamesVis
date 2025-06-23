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

st.title("🏆 Baby names popularity evolution over time in France")

# Chargement des données
df = load_and_clean_data(DATA_FILE)
df['annais'] = df['annais'].astype(int)

info_df = pd.read_csv(INFO_FILE)
info_df['year'] = info_df['year'].astype(int)

# One unified slider for all components
min_year = df['annais'].min()
max_year = df['annais'].max()

selected_year = st.slider("Select a year", min_value=min_year, max_value=max_year, value=1900, step=1)

# Nom cible
raw_input = st.text_input("Follow a name :", value="", placeholder="ex: Emma")
prenom_cible = normalize_prenom(raw_input.strip())

show_last_10 = st.checkbox("Display the 10 least popular names", value=False)

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
            x=alt.X('nombre:Q', title='Number or births'),
            y=alt.Y('rang_label:N', sort='-x', title='Name'),
            color=alt.condition('datum.is_target', alt.value('crimson'), alt.value('steelblue')),
            tooltip=['rang', 'preusuel', 'nombre']
        )
        .transform_filter(alt.datum.annais == selected_year)
        .properties(
            title=f"Ranking around {raw_input.strip().capitalize()} in {selected_year}",
            height=400
        )
    )
    st.subheader(f"Ranking around '{raw_input.strip().capitalize()}' in {selected_year}")

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
        title=f"Ranking evolution and number of births for {raw_input.strip().capitalize()}",
        height=400,
        width=800
    ).interactive()
    st.subheader(f"Ranking evolution and number of births for '{raw_input.strip().capitalize()}'")

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
        chart_title = "Ranking of the LEAST popular names"
    else:
        top_per_year = (
            top_per_year.groupby('annais', group_keys=False, observed=True)
            .apply(lambda x: x.nlargest(10, 'nombre'))
            .reset_index(drop=True)
        )
        chart_title = "Ranking of the MOST popular names"

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
            x=alt.X('nombre:Q', title='Number of births'),
            y=alt.Y('rang_label:N', sort='-x', title=chart_title),
            tooltip=['rang', 'preusuel', 'nombre'],
            color=alt.Color('preusuel:N', legend=None)
        )
        .transform_filter(alt.datum.annais == selected_year)
        .properties(height=400)
    )
    st.subheader(f"🥇 Top ten names for the year {selected_year}" if not show_last_10 else f"Least popular ten names for the year {selected_year}")

    st.altair_chart(chart, use_container_width=True)


    # Compute top or bottom 10 names in the selected year only
    current_year_data = (
        df[df['annais'] == selected_year]
        .groupby('preusuel', as_index=False)['nombre']
        .sum()
    )

    if show_last_10:
        top_names = current_year_data.nsmallest(10, 'nombre')['preusuel'].tolist()
        chart_title = "Ranking of the LEAST popular names"
    else:
        top_names = current_year_data.nlargest(10, 'nombre')['preusuel'].tolist()
        chart_title = "Ranking of the MOST popular names"

    # Compute ranking per year for these names
    df_grouped = df.groupby(['annais', 'preusuel'], as_index=False)['nombre'].sum()

    df_grouped['rang'] = (
        df_grouped.groupby('annais')['nombre']
        .rank(method='first', ascending=False)
        .astype(int)
    )


    # Filter only the top names selected and restrict to ranks 1 to 10
    # top_names_df = df_grouped[
    #     (df_grouped['preusuel'].isin(top_names)) & (df_grouped['rang'] <= 10)
    # ]

    # Filter based on top or bottom names logic
    if show_last_10:
        top_names_df = df_grouped[df_grouped['preusuel'].isin(top_names)]
        chart_title = "Ranking evolution of the 10 least popular names"
    else:
        top_names_df = df_grouped[
            (df_grouped['preusuel'].isin(top_names)) & (df_grouped['rang'] <= 10)
        ]
        chart_title = "Ranking evolution of the 10 most popular names"


    

    # Line chart of ranking evolution
    rank_chart = (
        alt.Chart(top_names_df)
        .mark_line()
        .encode(
            x=alt.X('annais:O', title='Year'),
            y=alt.Y('rang:Q', scale=alt.Scale(reverse=True), title='Rank (1=Top)'),
            color='preusuel:N',
            tooltip=['annais', 'preusuel', 'rang']
        )
    )

    # Get the last year for each name to label the end of each line
    label_data = top_names_df.sort_values('annais').groupby('preusuel').head(1)

    line_labels = alt.Chart(label_data).mark_text(
        align='center',
        baseline='bottom',
        dx=5, 
        dy=-5  
    ).encode(
        x='annais:O',
        y='rang:Q',
        text='preusuel',
        color='preusuel:N'
    )


    # Vertical line for selected year
    vertical_line = (
        alt.Chart(pd.DataFrame({'annais': [selected_year]}))
        .mark_rule(color='red', strokeDash=[5, 5])
        .encode(x='annais:O')
    )

    # Combine line chart and vertical line
    # combined_chart = alt.layer(
    #     rank_chart, vertical_line
    # ).properties(
    #     title=f"Ranking evolution of 10 names in {selected_year}",
    #     height=400,
    #     width=800
    # ).interactive()

    # combined_chart = alt.layer(rank_chart, vertical_line).configure_view(
    #     stroke=None
    # ).configure_axis(
    #     labelFontSize=12,
    #     titleFontSize=14
    # ).configure_legend(
    #     titleFontSize=13,
    #     labelFontSize=12,
    #     orient='bottom'
    # ).properties(
    #     title=chart_title + f" in {selected_year}",
    #     height=450,
    #     width=850,
    #     padding={"top": 10, "bottom": 50, "left": 5, "right": 5}
    # ).interactive()

    combined_chart = alt.layer(
        rank_chart, vertical_line, line_labels
    ).properties(
        #title=f"Global evolution of the ranking of the top ten names of {selected_year}",
        height=450,
        width=850,
        padding={"top": 10, "left": 10, "right": 60, "bottom": 40}
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14,
        labelAngle=0
    ).configure_legend(
        orient='bottom',
        titleFontSize=14,
        labelFontSize=14
    ).configure_view(
        stroke=None, 
        clip=False
    ).interactive()

    st.subheader(f"📊 Global evolution of the ranking of the {'most' if not show_last_10 else 'least'} popular ten names in {selected_year}")


    st.altair_chart(combined_chart, use_container_width=True)


# Info panel (uses the same selected_year)
info_row = info_df[info_df['year'] == selected_year]

if not info_row.empty:
    st.sidebar.markdown("### ℹ️ Key insights")
    st.sidebar.info(info_row.iloc[0]['info'])
else:
    st.sidebar.info("No information available for this year.")
