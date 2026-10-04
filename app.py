import streamlit as st
import pandas as pd
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
# READ GEOJSON DIRECTLY
# ==========================================

with open(
    "Maharashtra_Districts_36.geojson",
    "r",
    encoding="utf-8"
) as f:

    geojson = json.load(f)


# ==========================================
# CREATE DISTRICT LABEL POSITIONS
# ==========================================

def get_all_points(coords):

    points = []

    def extract(obj):

        if isinstance(obj, (list, tuple)):

            if (
                len(obj) >= 2
                and isinstance(obj[0], (int, float))
            ):

                points.append(
                    (obj[0], obj[1])
                )

            else:

                for item in obj:
                    extract(item)

    extract(coords)

    return points


label_data = []

for feature in geojson["features"]:

    district_name = feature["properties"].get(
        "district"
    )

    geometry = feature["geometry"]

    if geometry is None:
        continue

    points = get_all_points(
        geometry["coordinates"]
    )

    if points:

        avg_lon = sum(
            p[0] for p in points
        ) / len(points)

        avg_lat = sum(
            p[1] for p in points
        ) / len(points)

        label_data.append(
            {
                "District": district_name,
                "lon": avg_lon,
                "lat": avg_lat
            }
        )


labels = pd.DataFrame(label_data)


# ==========================================
# MATCH RANK WITH DISTRICT
# ==========================================

labels = labels.merge(
    cci[
        ["District", "Rank"]
    ],
    left_on="District",
    right_on="District",
    how="left"
)


# ==========================================
# CCI MAP
# ==========================================

st.subheader(
    "Maharashtra District CCI Map"
)

fig = px.choropleth(

    cci,

    geojson=geojson,

    locations="District",

    featureidkey="properties.district",

    color="PCA_CCI",

    hover_name="District",

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
# DISTRICT NAME + RANK
# ==========================================

fig.add_trace(

    go.Scattergeo(

        lon=labels["lon"],

        lat=labels["lat"],

        text=[
            f"{name}<br>Rank: {rank}"
            for name, rank in zip(
                labels["District"],
                labels["Rank"]
            )
        ],

        mode="text",

        textfont=dict(
            size=9
        ),

        hoverinfo="text",

        hovertext=[
            f"{name}<br>Rank: {rank}"
            for name, rank in zip(
                labels["District"],
                labels["Rank"]
            )
        ],

        showlegend=False
    )
)


# ==========================================
# MAP SETTINGS
# ==========================================

fig.update_geos(

    fitbounds="locations",

    visible=False
)


fig.update_layout(

    height=700,

    margin=dict(
        r=0,
        t=20,
        l=0,
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
# RANKING TABLE
# ==========================================

st.subheader("CCI Ranking")

ranking_table = cci.sort_values(
    "Rank"
).copy()

st.dataframe(

    ranking_table,

    use_container_width=True,

    hide_index=True
)


# ==========================================
# DOWNLOAD CCI RANKING
# ==========================================

csv_data = cci.to_csv(
    index=False
)

st.download_button(

    label="Download CCI Ranking (CSV)",

    data=csv_data,

    file_name="Maharashtra_CCI_Ranking.csv",

    mime="text/csv"
)
