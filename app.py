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

# ==========================================
# MERGE CCI DATA WITH MAP
# ==========================================

cci_map = cci[
    ["District", "PCA_CCI", "Rank",
     "Rainfall_Score", "Tmax_Score",
     "Tmin_Score", "DTR_Score"]
].copy()

cci_map["District"] = cci_map["District"].str.strip()
gdf["district"] = gdf["district"].str.strip()

gdf = gdf.merge(
    cci_map,
    left_on="district",
    right_on="District",
    how="left"
)
# ==========================================
# QUANTILE CLASSIFICATION
# ==========================================

q33 = gdf["PCA_CCI"].quantile(1/3)
q67 = gdf["PCA_CCI"].quantile(2/3)


def classify_cci(value):

    if value <= q33:
        return "Low"

    elif value <= q67:
        return "Moderate"

    else:
        return "High"


gdf["CCI_Category"] = gdf["PCA_CCI"].apply(classify_cci)

# ==========================================
# CREATE MAP
# ==========================================

m = folium.Map(
    location=[19.5, 75.5],
    zoom_start=6,
    tiles="CartoDB positron"
)


# ==========================================
# COLOURS
# ==========================================

def map_style(feature):

    category = feature["properties"]["CCI_Category"]

    if category == "Low":
        color = "red"

    elif category == "Moderate":
        color = "lightorange"

    else:
        color = "lightblue"

    return {
        "fillColor": color,
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.65
    }


# ==========================================
# ADD DISTRICTS TO MAP
# ==========================================

folium.GeoJson(
    gdf,
    name="CCI Classification",
    style_function=map_style,

    tooltip=folium.GeoJsonTooltip(
        fields=[
            "district",
            "PCA_CCI",
            "CCI_Category",
            "Rank"
        ],

        aliases=[
            "District:",
            "PCA CCI:",
            "Category:",
            "Rank:"
        ],

        localize=True
    )
).add_to(m)


# ==========================================
# SHOW CLASSIFICATION
# ==========================================

st.subheader("PCA Climate Change Index Classification")

st.write(f"33.33rd Percentile: {q33:.2f}")
st.write(f"66.67th Percentile: {q67:.2f}")

st.write(f"🟡 Low: PCA_CCI ≤ {q33:.2f}")
st.write(f"🟠 Moderate: {q33:.2f} < PCA_CCI ≤ {q67:.2f}")
st.write(f"🔴 High: PCA_CCI > {q67:.2f}")

# ==========================================
# DISPLAY MAP
# ==========================================

st.subheader("Maharashtra District Map")

st_folium(
    m,
    width=1200,
    height=650
)


# ==========================================
# RANKING TABLE
# ==========================================

st.subheader("CCI Ranking")

st.dataframe(cci)
