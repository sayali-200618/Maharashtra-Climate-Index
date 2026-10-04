import streamlit as st
import pandas as pd
import geopandas as gpd
import json
import plotly.express as px
import plotly.graph_objects as go

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
# PLOTLY MAHARASHTRA DISTRICT CCI MAP
# ==========================================

st.subheader("Maharashtra District CCI Map")

# Convert GeoDataFrame to proper GeoJSON
geojson_data = json.loads(gdf.to_json())

fig = px.choropleth(
    gdf,
    geojson=geojson_data,
    locations="district",
    featureidkey="properties.district",
    color="PCA_CCI",
    hover_name="district",
    hover_data={
        "PCA_CCI": ":.2f",
        "Rank": True,
        "Rainfall_Score": ":.2f",
        "Tmax_Score": ":.2f",
        "Tmin_Score": ":.2f",
        "DTR_Score": ":.2f"
    },
    color_continuous_scale="RdYlGn_r"
)

# ==========================================
# DISTRICT NAMES + RANK
# ==========================================

for _, row in gdf.iterrows():

    if row.geometry is not None and not row.geometry.is_empty:

        point = row.geometry.representative_point()

        fig.add_trace(
            go.Scattergeo(
                lon=[point.x],
                lat=[point.y],
                text=f"{row['district']}<br>Rank: {row['Rank']}",
                mode="text",
                textfont=dict(
                    size=9,
                    color="black"
                ),
                hoverinfo="skip",
                showlegend=False
            )
        )

# ==========================================
# FOCUS ONLY ON MAHARASHTRA
# ==========================================

fig.update_geos(
    fitbounds="locations",
    visible=False,
    projection_type="mercator"
)

fig.update_layout(
    height=700,
    margin=dict(
        l=0,
        r=0,
        t=20,
        b=0
    ),
    coloraxis_colorbar=dict(
        title="PCA CCI",
        thickness=20,
        len=0.7
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==========================================
# DOWNLOAD BUTTON
# ==========================================

csv_data = cci.to_csv(index=False)

st.download_button(
    label="Download CCI Ranking (CSV)",
    data=csv_data,
    file_name="Maharashtra_CCI_Ranking.csv",
    mime="text/csv"
)
