import streamlit as st
import pandas as pd
import numpy as np
from utils.preprocessing import Dataset, plot_stacked_area_chart, line_chart_mixed_names
from pathlib import Path

st.set_page_config(
    page_title="Visualization 3",
    layout="wide",
    initial_sidebar_state="expanded")

# ✅ Correction du chemin vers le CSV
current_dir = Path(__file__).resolve().parent       # .../src/pages
project_root = current_dir.parent.parent            # .../
csv_path = project_root / "data" / "raw" / "dpt2020.csv"

# Charger les données
df = pd.read_csv(csv_path, sep=';')
dataset = Dataset(df)
cleaned_df = dataset.get_cleaned_data()

# get all years
all_years = Dataset(cleaned_df).get_years()

# show graph
st.subheader("Evolution of Mixed Baby Names over the years")
# add radio box for 3 options: B, G or both
option = st.radio(label="",
         key='gender_selection',
         options=['Both', 'Boys', 'Girls'],
         horizontal=True)

cleaned_df_mixed = Dataset(cleaned_df).get_global_gender_counts()
print(cleaned_df_mixed.head())
if option == 'Boys':
    cleaned_df_mixed = cleaned_df_mixed[['annais', 'boys', 'mixed']]
elif option == 'Girls':
    cleaned_df_mixed = cleaned_df_mixed[['annais', 'girls', 'mixed']]

chart = line_chart_mixed_names(cleaned_df_mixed, all_years[0], all_years[-1])
st.altair_chart(chart, use_container_width=True)

st.subheader("TOP 10")

# name selection
all_names = Dataset(cleaned_df).get_names(sexe=None)
all_mixed_names = Dataset(cleaned_df).get_mixed_names()
print(f"All mixed names: {all_mixed_names}")
df_all_mixed_names = cleaned_df[cleaned_df['preusuel'].isin(all_mixed_names)]
name_input = st.text_input("Type a name:", "")

if name_input:
    name_selected = name_input.upper()
else:
    name_selected = None
    st.warning("No names found starting with that input.")

# year slider
start_year, end_year = st.select_slider(
    "Select year range:",
    options=all_years,
    value=(all_years[0], all_years[-1]))

print(f"Selected years: {start_year} to {end_year}")
if name_selected:
    # plot chart all dataset
    chart_selected_name = plot_stacked_area_chart(df_all_mixed_names, start_year, end_year, name_selected)
    st.altair_chart(chart_selected_name, use_container_width=True)
