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
# st.info(
#     """
#     In this page, we provide a tool to observe how evolve the baby names ever the years with impact of gender. So we define
# st.info(
#     """
#     In this page, we provide a tool to observe how evolve the baby names ever the years with impact of gender. So we define

#         Mixed name means a name used for both girls and boys.
#     """
# )
st.markdown(
    """
    <div style='text-align: center; background-color: #eaf6fb; padding: 1rem; border-radius: 0.5rem; color: black;'>
        <b>In this page, we provide a tool to observe how evolve the baby names over the years with impact of gender.</b><br><br>
        <i>Mixed name means a name used for both girls and boys.</i>
    </div>
    """,
    unsafe_allow_html=True
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
#----------------------------------------------------------------------
# graph 1: Area chart of Gender names & mixed names
#----------------------------------------------------------------------
# graph 1: Area chart of Gender names & mixed names
source = grouped_cleaned_df.copy()
# Map sexe to labels
mapping = {1: 'Boys', 2: 'Girls', 3: 'Boys mixed names', 4: 'Girls mixed names'}
color_scale = alt.Scale(
    domain=['Boys', 'Girls', 'Boys mixed names', 'Girls mixed names'],
    range=['#1f77b4', "#ef7c16", "#5c92b8",  "#e3a168"]  # Choisis tes couleurs ici
)
legends = {
    'Boys':"",
    'Girls':"Area for names that only girls have",
    'Boys mixed names':"area for names that are boys names but are also given to girls",
    'Girls mixed names':"area for names that are girls names but are also given to boys"
}
# Girls (sexe = 2 and 4 in dataframe)
sourceG = grouped_cleaned_df[grouped_cleaned_df['sexe'].isin([2, 4])].copy()
sourceG['sexe_label'] = sourceG['sexe'].map(mapping)
# Boys (sexe = 1 and 3 in dataframe)
# Boys (sexe = 1 and 3 in dataframe)
sourceB = grouped_cleaned_df[grouped_cleaned_df['sexe'].isin([1, 3])].copy()
sourceB['sexe_label'] = sourceB['sexe'].map(mapping)

# Graphique pour garçons (en haut)
areaB = alt.Chart(sourceB).mark_area().encode(
    x=alt.X("annais:T", title='Years').axis(format="%Y", orient="top", grid=True),
    y=alt.Y("nombre:Q", title="Boys"),
    color=alt.Color("sexe_label:N", title='', scale=color_scale, legend=alt.Legend(orient="bottom")),
).properties(height=200, width=900)

# Graphique pour filles (en bas, inversé)
areaG = alt.Chart(sourceG).mark_area().encode(
    x=alt.X("annais:T", title='Years').axis(format="%Y", grid=True),
    y=alt.Y("nombre:Q", scale=alt.Scale(reverse=True), title="Girls"),
    color=alt.Color("sexe_label:N",title='', scale=color_scale, legend=alt.Legend(orient="bottom")),
).properties(height=200, width=900)

# Empiler verticalement avec axe X partagé
chart = alt.vconcat(
    areaB,
    areaG
).resolve_scale(
    x='shared'
).configure_concat(
    spacing=0
).configure_legend(
    orient='bottom',  # position de la légende en bas
    padding=10,      # espace autour de la légende
    titleFontSize=16,
    labelFontSize=16
)
st.altair_chart(chart, use_container_width=True)
# st.markdown(
#     """
#     <div style='text-align: center; background-color: #eaf6fb; color: black;'>
#         <i>Boys = Area for names that only boys have</i>
#         <i>Girls = Area for names that only girls have</i>
#     </div>
#     """,
#     unsafe_allow_html=True
# )
st.info(
    """
    - Boys : Area for names that only boys have
    - Girls : Area for names that only girls have
    - Boys mixed names : area for names that are boys names but are also given to girls
    - Girls mixed names : area for names that are girls names but are also given to boys
    """
)
#----------------------------------------------------------------------
st.markdown(
    "<h3 style='text-align: center;'>Evolution of a mixte name over the years</h3>",
    unsafe_allow_html=True
)

#----------------------------------------------------------------------

col1, spacer, col2 = st.columns([1, 0.2, 2])
with col1:
    name_input = st.text_input("Type a name or choose one of list above:", "")
        #st.warning("No names found starting with that input.")
    # mixed_dt = Dataset(cleaned_df).get_dataset_by_gender(sexe='M')
    # mixed_dt = mixed_dt.groupby('preusuel')['nombre'].sum().reset_index(name='value')
    top_famous = ['CAMILLE', 'ALIX', 'CHARLIE', 'JESSY', 'MORGAN', 'CLAUDE', 'MARIE', 'LOUIS']
    pills_elements = pills("TOP FAMOUS NAMES",
                    top_famous,
                    ["👶🏼"]*len(top_famous),
                    index=None,)

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

    # st.markdown(f"""
    #         <div style='text-align: right; font-style: italic; color: #666;'>
    #         Click on a name from top famous to learn more""",
    #         unsafe_allow_html=True)
    if name_input:
        name_selected = name_input.upper()
    elif pills_elements:
        name_selected = pills_elements.upper()
    else:
        name_selected = "CAMILLE"
#----------------------------------------------------------------------
# graph 2
with col2: # plot function is called from preprocessing.py
    if name_selected:
        # plot chart all dataset
        # chart_selected_name = plot_stacked_area_chart(df_all_mixed_names, start_year, end_year, name_selected)
        st.markdown(
            f"""
            <div style='text-align: center; font-style: bold;'>
            <div style='text-align: center; font-style: bold;'>
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
        st.altair_chart(chart_selected_name, use_container_width=False)
