import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Maharashtra District Climate Map",
    layout="wide"
)

st.title("Maharashtra District Climate Map")

# --------------------------------------------------
# 1. READ EXCEL
# --------------------------------------------------

df = pd.read_excel(
     "Maharashtra_36_Districts_PCA_CCI_Final_Ranking.xlsx",
    sheet_name="Final_CCI_Ranking"
)

# --------------------------------------------------
# 2. READ GEOJSON
# --------------------------------------------------

with open("Maharashtra_Districts_36.geojson", "r", encoding="utf-8") as f:
    geojson = json.load(f)

# --------------------------------------------------
# 3. DISTRICT LABEL POSITIONS
# --------------------------------------------------

def get_all_points(coords):
    points = []

    def extract(obj):
        if isinstance(obj, (list, tuple)):
            if len(obj) >= 2 and isinstance(obj[0], (int, float)):
                points.append((obj[0], obj[1]))
            else:
                for item in obj:
                    extract(item)

    extract(coords)
    return points


label_data = []

for feature in geojson["features"]:

    district_name = feature["properties"].get("district")

    geometry = feature["geometry"]

    points = get_all_points(geometry["coordinates"])

    if points:
        avg_lon = sum(p[0] for p in points) / len(points)
        avg_lat = sum(p[1] for p in points) / len(points)

        label_data.append({
            "District": district_name,
            "lon": avg_lon,
            "lat": avg_lat
        })

labels = pd.DataFrame(label_data)

# --------------------------------------------------
# 4. MATCH RANK WITH DISTRICT
# --------------------------------------------------

labels = labels.merge(
    df[["District Name (district_name)", "Rank"]],
    left_on="District",
    right_on="District Name (district_name)",
    how="left"
)

# --------------------------------------------------
# 5. CHOROPLETH MAP
# --------------------------------------------------

st.subheader("District Accessibility Map")

fig = px.choropleth(
    df,
    geojson=geojson,
    locations="District Name (district_name)",
    featureidkey="properties.district",
    color="Overall Accessibility Score",
    hover_name="District Name (district_name)",
    hover_data={
        "Overall Accessibility Score": ":.4f",
        "Rank": True
    },
    color_continuous_scale="Viridis"
)

# --------------------------------------------------
# 6. PERMANENT DISTRICT NAME + RANK LABEL
# --------------------------------------------------

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

# --------------------------------------------------
# 7. MAP SETTINGS
# --------------------------------------------------

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

st.plotly_chart(
    fig,
    use_container_width=True
)

# --------------------------------------------------
# 8. RESULT TABLE
# --------------------------------------------------

st.subheader("District Accessibility Result")

st.dataframe(
    df,
    use_container_width=True
)
