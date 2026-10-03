import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# Page settings
st.set_page_config(
    page_title="Maharashtra Climate Change Index",
    layout="wide"
)

# Title
st.title("Maharashtra Climate Change Index")
st.write("District-wise Climate Change Index for Maharashtra (2000–2025)")

# Read CCI data
cci = pd.read_excel(
    "Maharashtra_Climate_Change_Index_COMPLETE.xlsx",
    sheet_name="CCI_Ranking"
)

# Read GeoJSON
gdf = gpd.read_file(
    "Maharashtra_Districts_36.geojson"
)

# Show basic information
st.write("Number of districts in GeoJSON:", len(gdf))
st.write("Number of districts in CCI data:", len(cci))

# Display CCI data
st.subheader("CCI Ranking")
st.dataframe(cci)
