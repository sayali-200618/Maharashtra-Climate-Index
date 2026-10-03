import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Maharashtra Climate Change Index",
    layout="wide"
)

st.title("Maharashtra Climate Change Index")
st.write("District-wise Climate Change Index for Maharashtra (2000–2025)")

# -----------------------------
# 1. Read CCI data
# -----------------------------
file = "Maharashtra_36_Districts_PCA_CCI_Final_Ranking.xlsx"

cci = pd.read_excel(
    file,
    sheet_name="Final_CCI_Ranking"
)

# -----------------------------
# 2. Read Maharashtra GeoJSON
# -----------------------------
gdf = gpd.read_file(
    "Maharashtra_Districts_36.geojson"
)

# -----------------------------
# 3. Check district names
# -----------------------------
st.write("CCI districts:", len(cci))
st.write("Map districts:", len(gdf))

# -----------------------------
# 4. Create map
# -----------------------------
m = folium.Map(
    location=[19.5, 75.5],
    zoom_start=6,
    tiles="CartoDB positron"
)

# -----------------------------
# 5. Add CCI values to map
# -----------------------------
folium.GeoJson(
    gdf,
    name="Maharashtra Districts",
    tooltip=folium.GeoJsonTooltip(
        fields=["district"],
        aliases=["District:"],
        localize=True
    )
).add_to(m)

# -----------------------------
# 6. Display map
# -----------------------------
st.subheader("Maharashtra District Map")

st_folium(
    m,
    width=1200,
    height=650
)

# -----------------------------
# 7. Show ranking table
# -----------------------------
st.subheader("CCI Ranking")

st.dataframe(cci)
