import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go


# --------------------------------------------------
# PAGE SETTINGS
# --------------------------------------------------

st.set_page_config(
    page_title="Maharashtra Climate Change Index",
    layout="wide"
)


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("Maharashtra District CCI Map")

st.write(
    "District-wise Climate Change Index for Maharashtra (2000–2025)"
)


# --------------------------------------------------
# READ CCI DATA
# --------------------------------------------------

file = "Maharashtra_36_Districts_PCA_CCI_Final_Ranking.xlsx"

cci = pd.read_excel(
    file,
    sheet_name="Final_CCI_Ranking"
)

cci["District"] = (
    cci["District"]
    .astype(str)
    .str.strip()
)


# --------------------------------------------------
# CREATE LOW / MODERATE / HIGH CATEGORIES
# --------------------------------------------------

q33 = cci["PCA_CCI"].quantile(0.33)
q67 = cci["PCA_CCI"].quantile(0.67)

cci["CCI_Category"] = pd.cut(
    cci["PCA_CCI"],
    bins=[
        -float("inf"),
        q33,
        q67,
        float("inf")
    ],
    labels=[
        "Low",
        "Moderate",
        "High"
    ]
)


# --------------------------------------------------
# READ GEOJSON
# --------------------------------------------------

with open(
    "Maharashtra_Districts_36.geojson",
    "r",
    encoding="utf-8"
) as f:

    geojson = json.load(f)


# --------------------------------------------------
# MAP TITLE
# --------------------------------------------------

st.subheader("Maharashtra District CCI Map")


# --------------------------------------------------
# CREATE CHOROPLETH MAP
# --------------------------------------------------

fig = px.choropleth(

    cci,

    geojson=geojson,

    locations="District",

    featureidkey="properties.district",

    color="CCI_Category",

    color_discrete_map={
        "Low": "yellow",
        "Moderate": "orange",
        "High": "red"
    },

    hover_name="District",

    hover_data={
        "PCA_CCI": ":.2f",
        "Rank": True,
        "CCI_Category": True,
        "Rainfall_Score": ":.2f",
        "Tmax_Score": ":.2f",
        "Tmin_Score": ":.2f",
        "DTR_Score": ":.2f"
    }

)


# --------------------------------------------------
# FIND LABEL POSITIONS
# --------------------------------------------------

label_data = []


def get_points(coordinates):

    points = []

    def extract(obj):

        if isinstance(obj, (list, tuple)):

            # Check whether this is [longitude, latitude]
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


# --------------------------------------------------
# CREATE DISTRICT LABELS
# --------------------------------------------------

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


# --------------------------------------------------
# ADD RANK TO LABEL DATA
# --------------------------------------------------

labels = labels.merge(
    cci[
        [
            "District",
            "Rank"
        ]
    ],

    on="District",

    how="left"
)


# --------------------------------------------------
# ADD DISTRICT NAME + RANK ON MAP
# --------------------------------------------------

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


# --------------------------------------------------
# ZOOM TO MAHARASHTRA
# --------------------------------------------------

fig.update_geos(

    fitbounds="locations",

    visible=False,

    projection_type="mercator",

    bgcolor="white",

    showland=False,

    showocean=False

)


# --------------------------------------------------
# MAP LAYOUT
# --------------------------------------------------

fig.update_layout(

    geo=dict(

        center=dict(
            lat=19.5,
            lon=75.5
        ),

        projection_scale=7

    ),

    height=700,

    margin=dict(
        l=0,
        r=0,
        t=20,
        b=0
    ),

    paper_bgcolor="white",

    legend=dict(
        title="CCI Category"
    )

)


# --------------------------------------------------
# DISPLAY MAP
# --------------------------------------------------

st.plotly_chart(
    fig,
    use_container_width=True
)


# --------------------------------------------------
# CATEGORY SUMMARY
# --------------------------------------------------

st.subheader("CCI Category Summary")

category_summary = (
    cci["CCI_Category"]
    .value_counts()
    .reindex(
        ["Low", "Moderate", "High"],
        fill_value=0
    )
    .reset_index()
)

category_summary.columns = [
    "CCI Category",
    "Number of Districts"
]

st.dataframe(
    category_summary,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# CCI RANKING
# --------------------------------------------------

st.subheader("CCI Ranking")

ranking_table = (
    cci
    .sort_values("Rank")
    .copy()
)

st.dataframe(
    ranking_table,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# DOWNLOAD CSV
# --------------------------------------------------

csv_data = cci.to_csv(
    index=False
)

st.download_button(

    label="Download CCI Ranking (CSV)",

    data=csv_data,

    file_name="Maharashtra_CCI_Ranking.csv",

    mime="text/csv"

)
