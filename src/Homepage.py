import streamlit as st
from pathlib import Path

# Set page config
st.set_page_config(page_title="My App Home", layout="wide")

# Title
st.title("Welcome to our Babynames visualization app")

# Path to images
img_dir = Path("images")

# Create three columns
col1, col2, col3 = st.columns(3)

# Page 1 Block
with col1:
    st.image(str(img_dir / "baby1.jpg"))
    st.image(str(img_dir / "visu1.png"))#, use_container_width=True)
    if st.button("Go to Visualization 1"):
        st.switch_page("pages/visualization1.py")

# Page 2 Block
with col2:
    st.image(str(img_dir / "baby2.jpg"))
    st.image(str(img_dir / "visu1.png"))#, use_container_width=True)
    if st.button("Go to Visualization 2"):
        st.switch_page("pages/visualization2.py")

# Page 3 Block
with col3:
    st.image(str(img_dir / "baby3.jpg"))
    st.image(str(img_dir / "visu1.png"))#, use_container_width=True)
    if st.button("Go to Visualisation 3"):
        st.switch_page("pages/visualization3.py")
