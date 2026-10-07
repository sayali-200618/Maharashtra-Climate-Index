import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from shapely.geometry import shape

# =========================================================
# PLOTLY VERSION COMPATIBILITY HELPER
# =========================================================
# Robustly grab the Mapbox classes supporting both Plotly v5 and v6
try:
    ChoroplethMapboxClass = go.ChoroplethMapbox
except AttributeError:
    ChoroplethMapboxClass = go.Choroplethmapbox

try:
    ScatterMapboxClass = go.ScatterMapbox
except AttributeError:
    ScatterMapboxClass = go.Scattermapbox

# =========================================================
# PAGE SETTINGS
# =========================================================
st.set_page_config(
    page_title="Maharashtra Climate Change Index",
    layout="wide"
)

st.title("Maharashtra Climate Change Index")
st.write("District-wise Climate Change Index for Maharashtra (2000–2025)")

# =========================================================
# 1. READ EXCEL FILE
# =========================================================
excel_file = "Maharashtra_36_Districts_PCA_CCI_Final_Ranking.xlsx"
try:
    df = pd.read_excel(
        excel_file,
        sheet_name="Final_CCI_Ranking"
    )
except Exception as e:
    st.error(f"Could not find or read {excel_file}. Please ensure you upload this file to Colab. Error: {e}")
    st.stop()

# =========================================================
# 2. CHECK REQUIRED COLUMNS
# =========================================================
required_columns = [
    "District",
    "PCA_CCI",
    "Rank",
    "Rainfall_Score",
    "Tmax_Score",
    "Tmin_Score",
    "DTR_Score"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(
        "These columns are missing from the Excel file: "
        + ", ".join(missing_columns)
    )
    st.stop()

# =========================================================
# 3. CLEAN DISTRICT NAMES
# =========================================================
df["District"] = (
    df["District"]
    .astype(str)
    .str.strip()
)

# =========================================================
# 4. READ GEOJSON
# =========================================================
geojson_file = "Maharashtra_Districts_36.geojson"
try:
    with open(
        geojson_file,
        "r",
        encoding="utf-8"
    ) as f:
        geojson = json.load(f)
except Exception as e:
    st.error(f"Could not find or read {geojson_file}. Please run the previous notebook cells to build it first. Error: {e}")
    st.stop()

# =========================================================
# 5. NORMALIZE DISTRICT NAMES
# =========================================================
name_changes = {
    "Chhatrapati Sambhaji Nagar": "Aurangabad",
    "Chhatrapati Sambhajinagar": "Aurangabad",
    "Sambhajinagar": "Aurangabad",
    "Ahilyanagar": "Ahmednagar"
}

df["GeoDistrict"] = (
    df["District"]
    .replace(name_changes)
    .str.strip()
)

# =========================================================
# 7. QUANTILE CLASSIFICATION
# =========================================================
q33 = df["PCA_CCI"].quantile(1 / 3)
q67 = df["PCA_CCI"].quantile(2 / 3)

def classify_cci(value):
    if value <= q33:
        return "Low"
    elif value <= q67:
        return "Moderate"
    else:
        return "High"

df["CCI_Category"] = df["PCA_CCI"].apply(classify_cci)

# =========================================================
# 8. CREATE DISTRICT LABEL POSITIONS
# =========================================================
label_data = []
for feature in geojson["features"]:
    district_name = str(feature["properties"].get("district")).strip()
    geometry = feature.get("geometry")
    if geometry is None:
        continue
    polygon = shape(geometry)
    point = polygon.representative_point()
    label_data.append({
        "GeoDistrict": district_name,
        "lon": point.x,
        "lat": point.y
    })

labels = pd.DataFrame(label_data)

# =========================================================
# 9. ADD RANK TO LABEL DATA
# =========================================================
labels = labels.merge(
    df[["GeoDistrict", "District", "Rank"]],
    on="GeoDistrict",
    how="left"
)

# =========================================================
# 10. CREATE MAP
# =========================================================
st.subheader("Maharashtra District Climate Change Map")
fig = go.Figure()

category_colors = {
    "Low": "#FFFF80",       # Soft, clean yellow
    "Moderate": "#FFA500",  # Vibrant orange
    "High": "#FF4D4D",      # Warning red
}

# Calculate center of Maharashtra dynamically to center our mapbox
mean_lat = labels["lat"].mean() if not labels.empty else 19.7
mean_lon = labels[]
