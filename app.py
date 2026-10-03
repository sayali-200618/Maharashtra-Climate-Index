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
# EQUAL INTERVAL CLASSIFICATION
# ==========================================

min_cci = gdf["PCA_CCI"].min()
max_cci = gdf["PCA_CCI"].max()

interval = (max_cci - min_cci) / 3

low_max = min_cci + interval
moderate_max = min_cci + (2 * interval)


def classify_cci(value):

    if value <= low_max:
        return "Low"

    elif value <= moderate_max:
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
        color = "maroon"

    else:
        color = "pink"

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

st.write(f"Minimum PCA_CCI: {min_cci:.2f}")
st.write(f"Maximum PCA_CCI: {max_cci:.2f}")

st.write(f"🟡 Low: {min_cci:.2f} – {low_max:.2f}")
st.write(f"🟠 Moderate: {low_max:.2f} – {moderate_max:.2f}")
st.write(f"🔴 High: {moderate_max:.2f} – {max_cci:.2f}")


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
