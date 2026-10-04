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
    tiles="CartoDB positron",
    dragging=False,
    scrollWheelZoom=True,
    doubleClickZoom=True,
    zoomControl=True
)


# ==========================================
# COLOURS
# ==========================================

def map_style(feature):

    category = feature["properties"]["CCI_Category"]

    if category == "Low":
        color = "yellow"

    elif category == "Moderate":
        color = "orange"

    else:
        color = "red"

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
# ADD DISTRICT NAMES
# ==========================================

for _, row in gdf.iterrows():

    if row.geometry is not None and not row.geometry.is_empty:

        point = row.geometry.representative_point()

        folium.map.Marker(
            [point.y, point.x],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    font-size: 9px;
                    font-weight: bold;
                    color: black;
                    text-align: center;
                    white-space: nowrap;
                ">
                    {row["district"]}
                </div>
                """
            )
        ).add_to(m)
# ==========================================
# MAP LEGEND
# ==========================================

legend_html = f"""
<div style="
    position: fixed;
    bottom: 30px;
    right: 30px;
    z-index: 9999;
    background-color: white;
    border: 2px solid grey;
    border-radius: 5px;
    padding: 10px;
    font-size: 13px;
">

<b>CCI Category</b><br><br>

<div>
<span style="
    background-color: yellow;
    width: 18px;
    height: 18px;
    display: inline-block;
    margin-right: 6px;
"></span>
Low: ≤ {q33:.2f}
</div>

<div>
<span style="
    background-color: orange;
    width: 18px;
    height: 18px;
    display: inline-block;
    margin-right: 6px;
"></span>
Moderate: > {q33:.2f} – ≤ {q67:.2f}
</div>

<div>
<span style="
    background-color: red;
    width: 18px;
    height: 18px;
    display: inline-block;
    margin-right: 6px;
"></span>
High: > {q67:.2f}
</div>

</div>
"""

m.get_root().html.add_child(
    folium.Element(legend_html)
)
# ==========================================
# CATEGORY SUMMARY
# ==========================================

low_count = (gdf["CCI_Category"] == "Low").sum()
moderate_count = (gdf["CCI_Category"] == "Moderate").sum()
high_count = (gdf["CCI_Category"] == "High").sum()

st.subheader("CCI Category Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Low", low_count)

with col2:
    st.metric("Moderate", moderate_count)

with col3:
    st.metric("High", high_count)
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
# ==========================================
# DOWNLOAD CCI RANKING
# ==========================================

csv_data = cci.to_csv(index=False)

st.download_button(
    label="Download CCI Ranking (CSV)",
    data=csv_data,
    file_name="Maharashtra_CCI_Ranking.csv",
    mime="text/csv"
)
