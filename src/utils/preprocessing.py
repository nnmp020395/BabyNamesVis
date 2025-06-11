"""
Preprocessing functions for the 3 visualizations
"""
import pandas as pd

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






###############################################################################
# Visualisation 3
###############################################################################
