import streamlit as st
import pandas as pd
import geopandas as gpd
import json
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
    [
        "District",
        "PCA_CCI",
        "Rank",
        "Rainfall_Score",
        "Tmax_Score",
        "Tmin_Score",
        "DTR_Score"
    ]
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

q33 = gdf["PCA_CCI"].quantile(1 / 3)
q67 = gdf["PCA_CCI"].quantile(2 / 3)


def classify_cci(value):

    if value <= q33:
        return "Low"

    elif value <= q67:
        return "Moderate"

    else:
        return "High"


gdf["CCI_Category"] = gdf["PCA_CCI"].apply(classify_cci)

# ==========================================
# MAHARASHTRA DISTRICT CCI MAP
# ==========================================

st.subheader("Maharashtra District CCI Map")

# Convert GeoDataFrame to GeoJSON
geojson_data = json.loads(gdf.to_json())

fig = go.Figure()

# ==========================================
# DISTRICT POLYGONS
# ==========================================

fig.add_trace(
    go.Choropleth(
        geojson=geojson_data,
        locations=gdf["district"],
        z=gdf["PCA_CCI"],
        featureidkey="properties.district",
        colorscale="RdYlGn_r",
        marker_line_color="black",
        marker_line_width=0.7,
        colorbar=dict(
            title="PCA CCI"
        ),
        hovertemplate=
            "<b>%{location}</b><br>" +
            "PCA CCI: %{z:.2f}<br>" +
            "<extra></extra>"
    )
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
                    size=8,
                    color="black"
                ),
                hoverinfo="skip",
                showlegend=False
            )
        )

# ==========================================
# NORTH ARROW
# ==========================================

fig.add_annotation(
    x=0.94,
    y=0.18,
    ax=0.94,
    ay=0.30,
    xref="paper",
    yref="paper",
    axref="paper",
    ayref="paper",
    text="N",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=3,
    arrowcolor="black",
    font=dict(
        size=18,
        color="black"
    )
)

# ==========================================
# MAP SETTINGS
# ==========================================

fig.update_geos(
    fitbounds="locations",
    visible=False,
    projection_type="mercator",
    bgcolor="white"
)

fig.update_layout(
    height=700,
    margin=dict(
        l=0,
        r=0,
        t=20,
        b=0
    )
)

# ==========================================
# DISPLAY MAP
# ==========================================

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==========================================
# DOWNLOAD MAP AS PNG
# ==========================================

map_image = fig.to_image(
    format="png",
    width=1400,
    height=900,
    scale=2
)

st.download_button(
    label="Download Map as PNG",
    data=map_image,
    file_name="Maharashtra_CCI_Map.png",
    mime="image/png"
)

# ==========================================
# RANKING TABLE
# ==========================================

st.subheader("CCI Ranking")

ranking_table = cci.sort_values("Rank").copy()

st.dataframe(
    ranking_table,
    use_container_width=True,
    hide_index=True
)

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
