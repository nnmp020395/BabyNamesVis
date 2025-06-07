import streamlit as st
import pandas as pd
import bar_chart_race as bcr
import os
import tempfile
from utils.preprocessing import load_and_clean_data

st.title("Évolution de la popularité des prénoms en France")

# Chargement des données
df = load_and_clean_data("data/dpt2020.csv")

# Années 
min_year = df['annais'].min()
max_year = df['annais'].max()

# Curseur
year_range = st.slider("Sélectionnez une plage d'années", min_value=min_year, max_value=max_year, value=(min_year, max_year))

# Filtrage sur la plage d'années
df_filtered = df[(df['annais'] >= year_range[0]) & (df['annais'] <= year_range[1])]

# Somme des naissances par prénom et année
df_race = df_filtered.groupby(['annais', 'preusuel'])['nombre'].sum().unstack(fill_value=0)

# Au clic !
if st.button("Générer le graphique animé"):
    with st.spinner("Génération en cours..."):
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmpfile:
            output_path = tmpfile.name

            bcr.bar_chart_race(
                df=df_race,
                filename=output_path,
                orientation='h',
                sort='desc',
                n_bars=10,
                fixed_order=False,
                fixed_max=True,
                steps_per_period=20,
                interpolate_period=False,
                label_bars=True,
                bar_size=.95,
                period_label={'x': .99, 'y': .25, 'ha': 'right', 'va': 'center'},
                period_fmt='%y',
                period_length=500,
                figsize=(5, 3),
                dpi=144,
                cmap='dark12',
                title=f"Top 10 des prénoms en France ({year_range[0]}–{year_range[1]})",
            )

        # Lecture et affichage de la vidéo
        with open(output_path, 'rb') as f:
            st.video(f.read())
