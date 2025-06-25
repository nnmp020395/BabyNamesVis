import streamlit as st
import pandas as pd
import numpy as np
from utils.preprocessing import (
    Dataset,
    plot_stacked_area_chart,
    line_chart_mixed_names,
    multi_line_tooltip_by_gender,
    heatmap_line_percent,

)
import altair as alt
alt.data_transformers.enable('json')
from pathlib import Path
from streamlit_pills import pills

# Get path to project root (one level up from src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "dpt2020.csv"

st.set_page_config(
    page_title="Visualization 3",
    layout="wide",
    initial_sidebar_state="expanded")

st.title("Evolution of Baby Names by Gender over the years")
st.info(
    """
    In this page, we provide a tool to observe how evolve the baby names ever the years with impact of gender. So we define

        - mixed name means a name that was used on baby girl and baby boy

        - mixed boys or mixed girls mean a boy name is used like name for baby girls.
    """
)

# Charger les données
df = pd.read_csv(DATA_FILE, sep=';')
dataset = Dataset(df)
cleaned_df = dataset.get_cleaned_data()
mixed_cleaned_df = Dataset(cleaned_df).get_dataset_by_gender(sexe='M')

mixed_names = Dataset(cleaned_df).get_mixed_names()
no_mixed_cleaned_df = cleaned_df[~cleaned_df['preusuel'].isin(mixed_names)]

mixed_cleaned_df['sexe'] = mixed_cleaned_df['sexe'].replace(2, 4) # G to MG
mixed_cleaned_df['sexe'] = mixed_cleaned_df['sexe'].replace(1, 3) # B to MB

new_cleaned_df = pd.concat([cleaned_df, mixed_cleaned_df])

grouped_cleaned_df = new_cleaned_df.groupby(['annais', 'sexe'])['nombre'].sum().reset_index()


# get all years
all_years = Dataset(cleaned_df).get_years()

# show graph

# add radio box for 3 options: B, G or both
# option = st.radio(label="",
#          key='gender_selection',
#          options=['Both', 'Boys', 'Girls'],
#          horizontal=True)

# cleaned_df_mixed = Dataset(cleaned_df).get_global_gender_counts()
source = grouped_cleaned_df.copy()

# if option == 'Boys':
#     # cleaned_df_mixed = cleaned_df_mixed[['annais', 'boys', 'mixed']]
#     source = grouped_cleaned_df[grouped_cleaned_df['sexe'].isin([1,3])] # where data have 4 classes: B, G, Mixed B, Mixed D
# elif option == 'Girls':
#     # cleaned_df_mixed = cleaned_df_mixed[['annais', 'girls', 'mixed']]
#     source = grouped_cleaned_df[grouped_cleaned_df['sexe'].isin([2,4])]

# chart = line_chart_mixed_names(cleaned_df_mixed, all_years[0], all_years[-1])
sourceG = grouped_cleaned_df[grouped_cleaned_df['sexe'].isin([2, 4])].copy()
mapping = {1: 'A-Boys', 2: 'B-Girls', 3: 'C-Boys mixed names', 4: 'D-Girls mixed names'}
sourceG['sexe_label'] = sourceG['sexe'].map(mapping)

# Garçons (sexe 1 et 3)
sourceB = grouped_cleaned_df[grouped_cleaned_df['sexe'].isin([1, 3])].copy()
sourceB['sexe_label'] = sourceB['sexe'].map(mapping)

# Graphique pour garçons (en haut)
areaB = alt.Chart(sourceB).mark_area().encode(
    x=alt.X("annais:T", title='Years').axis(format="%Y", orient="top", grid=True),
    y=alt.Y("nombre:Q", title="Boys"),
    color=alt.Color("sexe_label:N", title='Label'),
).properties(height=200, width=800)

# Graphique pour filles (en bas, inversé)
areaG = alt.Chart(sourceG).mark_area().encode(
    x=alt.X("annais:T", title='Years').axis(format="%Y", grid=True),
    y=alt.Y("nombre:Q", scale=alt.Scale(reverse=True), title="Girls"),
    color=alt.Color("sexe_label:N", title='Label'),
).properties(height=200, width=800)

# Empiler verticalement avec axe X partagé
chart = alt.vconcat(areaB, areaG).resolve_scale(x='shared').configure_concat(spacing=0)
st.altair_chart(chart, use_container_width=True)

st.subheader("Top 10 mixed names over the years")
mixed_dt = Dataset(cleaned_df).get_dataset_by_gender(sexe='M')
mixed_dt = mixed_dt.groupby('preusuel')['nombre'].sum().reset_index(name='value')
pills_elements = pills("",
                mixed_dt.sort_values(by='value', ascending=False)['preusuel'].tolist()[:10],
                ["👶🏼"]*10,
                index=None,)
st.write("Click a name of list and see how it changes")

st.subheader('Focus on a name')
col1, col2 = st.columns([1, 2])
with col1:
    name_input = st.text_input("Type a name or choose one of list above:", "")
    if name_input:
        name_selected = name_input.upper()
    elif pills_elements:
        name_selected = pills_elements.upper()
    else:
        name_selected = "CAMILLE"
        #st.warning("No names found starting with that input.")

    st.write('Select year ranges')
    start_year = st.selectbox("Start year:", options=all_years, index=0)
    end_year = st.selectbox("End year:", options=all_years, index=len(all_years)-1)
    st.markdown(
        f"""
        <div style='text-align: right; font-style: italic; color: #666;'>
        {'You select ' + str(start_year) + ' to ' + str(end_year)}</div>
        """,
        unsafe_allow_html=True
    )

with col2:
    if name_selected:
        # plot chart all dataset
        # chart_selected_name = plot_stacked_area_chart(df_all_mixed_names, start_year, end_year, name_selected)
        st.markdown(
            f"""
            <div style='text-align: center; font-style: bold; color: #666;'>
            {'Evolution of '+ name_selected.upper() + ' between ' + str(start_year) + ' and ' + str(end_year)}</div>
            """,
            unsafe_allow_html=True
        )
        df_selected = mixed_cleaned_df[mixed_cleaned_df['preusuel'] == name_selected]
        df_pct = Dataset(df_selected).convert_to_pct()
        if start_year and end_year:
            df_pct = df_pct[(df_pct['annais'] >= start_year) & (df_pct['annais'] <= end_year)]
        print(df_pct)
        chart_selected_name = heatmap_line_percent(mixed_cleaned_df, df_pct)
        st.altair_chart(chart_selected_name, use_container_width=True)