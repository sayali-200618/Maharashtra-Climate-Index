import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go


# ==========================================
# PAGE SETTINGS
# ==========================================

st.set_page_config(
    page_title="Maharashtra Climate Change Index",
    layout="wide"
)

st.title("Maharashtra Climate Change Index")

st.write(
    "District-wise Climate Change Index for Maharashtra (2000–2025)"
)


# ==========================================
# 1. READ CCI DATA
# ==========================================

file = "Maharashtra_36_Districts_PCA_CCI_Final_Ranking.xlsx"

cci = pd.read_excel(
    file,
    sheet_name="Final_CCI_Ranking"
)

# Remove extra spaces from district names
cci["District"] = cci["District"].astype(str).str.strip()


# ==========================================
# 2. READ MAHARASHTRA GEOJSON
# ==========================================

with open(
    "Maharashtra_Districts_36.geojson",
    "r",
    encoding="utf-8"
) as f:

    geojson = json.load(f)


# ==========================================
# 3. CCI MAP
# ==========================================

st.subheader("Maharashtra District CCI Map")


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
# 4. DISTRICT LABELS + RANK
# ==========================================

label_data = []


def get_points(coordinates):

    points = []

    def extract(obj):

        if isinstance(obj, (list, tuple)):

            if (
                len(obj) >= 2
                and isinstance(obj[0], (int, float))
                and isinstance(obj[1], (int, float))
            ):

                points.append(
                    (obj[0], obj[1])
                )

            else:

                for item in obj:
                    extract(item)

    extract(coordinates)

    return points


for feature in geojson["features"]:

    district_name = feature["properties"].get(
        "district"
    )

    geometry = feature.get("geometry")

    if geometry is None:
        continue

    points = get_points(
        geometry["coordinates"]
    )

    if len(points) == 0:
        continue

    longitude = sum(
        point[0] for point in points
    ) / len(points)

    latitude = sum(
        point[1] for point in points
    ) / len(points)

    label_data.append(
        {
            "District": district_name,
            "lon": longitude,
            "lat": latitude
        }
    )


labels = pd.DataFrame(label_data)


# Match rank with district
labels = labels.merge(
    cci[
        ["District", "Rank"]
    ],
    on="District",
    how="left"
)


# ==========================================
# 5. ADD DISTRICT NAMES AND RANKS
# ==========================================

fig.add_trace(

    go.Scattergeo(

        lon=labels["lon"],

        lat=labels["lat"],

        text=[
            f"{district}<br>Rank: {rank}"
            for district, rank
            in zip(
                labels["District"],
                labels["Rank"]
            )
        ],

        mode="text",

        textfont=dict(
            size=8,
            color="black"
        ),

        hoverinfo="text",

        showlegend=False
    )
)


# ==========================================
# 6. MAP SETTINGS
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

    paper_bgcolor="white"
)


# ==========================================
# 7. DISPLAY MAP
# ==========================================

st.plotly_chart(
    fig,
    use_container_width=True
)


# ==========================================
# 8. CCI RANKING TABLE
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
# 9. DOWNLOAD CCI RANKING
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
