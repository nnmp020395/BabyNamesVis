import streamlit as st
from pathlib import Path

# Set page config
st.set_page_config(page_title="My App Home", layout="wide")

# Title
st.title("Welcome to My Streamlit App")

# Path to images
img_dir = Path("images")

# Create three columns
col1, col2, col3 = st.columns(3)

# Page 1 Block
with col1:
    st.image(img_dir / "visu1.png", use_container_width=True)
    if st.button("Go to Page 1"):
        st.switch_page("pages/visualization1.py")

# Page 2 Block
with col2:
    st.image(img_dir / "visu1.png", use_container_width=True)
    if st.button("Go to Page 2"):
        st.switch_page("pages/visualization2.py")

# Page 3 Block
with col3:
    st.image(img_dir / "visu1.png", use_container_width=True)
    if st.button("Go to Page 3"):
        st.switch_page("pages/visualization3.py")
