import streamlit as st
import pandas as pd
import json
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
# DISTRICT NAME MATCHING
# --------------------------------------------------

name_changes = {
    "Chhatrapati Sambhaji Nagar": "Aurangabad",
    "Chhatrapati Sambhajinagar": "Aurangabad",
    "Sambhajinagar": "Aurangabad",
    "Ahilyanagar": "Ahmednagar"
}

cci["GeoDistrict"] = (
    cci["District"]
    .replace(name_changes)
)


# --------------------------------------------------
# LOW / MODERATE / HIGH CLASSIFICATION
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
# CREATE MAP
# --------------------------------------------------

fig = go.Figure()


# --------------------------------------------------
# COLOURS
# --------------------------------------------------

category_colors = {
    "Low": "yellow",
    "Moderate": "orange",
    "High": "red"
}


# --------------------------------------------------
# ADD DISTRICT POLYGONS
# --------------------------------------------------

for category in ["Low", "Moderate", "High"]:

    data = cci[
        cci["CCI_Category"] == category
    ].copy()

    if data.empty:
        continue

    customdata = data[
        [
            "District",
            "PCA_CCI",
            "Rank",
            "Rainfall_Score",
            "Tmax_Score",
            "Tmin_Score",
            "DTR_Score"
        ]
    ].values

    fig.add_trace(
        go.Choropleth(
            geojson=geojson,

            locations=data["GeoDistrict"],

            z=[1] * len(data),

            featureidkey="properties.district",

            colorscale=[
                [0, category_colors[category]],
                [1, category_colors[category]]
            ],

            zmin=0,
            zmax=1,

            showscale=False,

            name=category,

            marker_line_color="black",

            marker_line_width=0.8,

            customdata=customdata,

            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "CCI: %{customdata[1]:.2f}<br>"
                "Rank: %{customdata[2]}<br>"
                "Category: " + category + "<br>"
                "Rainfall Score: %{customdata[3]:.2f}<br>"
                "Tmax Score: %{customdata[4]:.2f}<br>"
                "Tmin Score: %{customdata[5]:.2f}<br>"
                "DTR Score: %{customdata[6]:.2f}"
                "<extra></extra>"
            )
        )
    )


# --------------------------------------------------
# FIND DISTRICT LABEL POSITIONS
# --------------------------------------------------

label_data = []


def extract_points(obj, points):

    if isinstance(obj, list):

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
                extract_points(item, points)


for feature in geojson["features"]:

    district = feature["properties"]["district"]

    points = []

    extract_points(
        feature["geometry"]["coordinates"],
        points
    )

    if not points:
        continue

    lon = sum(
        p[0] for p in points
    ) / len(points)

    lat = sum(
        p[1] for p in points
    ) / len(points)

    label_data.append(
        {
            "GeoDistrict": district,
            "lon": lon,
            "lat": lat
        }
    )


labels = pd.DataFrame(label_data)


# --------------------------------------------------
# ADD CCI INFORMATION TO LABELS
# --------------------------------------------------

labels = labels.merge(
    cci[
        [
            "GeoDistrict",
            "District",
            "Rank"
        ]
    ],
    on="GeoDistrict",
    how="left"
)


# --------------------------------------------------
# DISTRICT NAME + RANK
# --------------------------------------------------

fig.add_trace(
    go.Scattergeo(
        lon=labels["lon"],
        lat=labels["lat"],

        text=[
            f"{district}<br>{int(rank)}"
            if pd.notna(rank)
            else district
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

        hoverinfo="skip",

        showlegend=False
    )
)


# --------------------------------------------------
# MAHARASHTRA ZOOM-IN
# --------------------------------------------------

fig.update_geos(
    visible=False,

    projection_type="mercator",

    center=dict(
        lat=19.2,
        lon=76.3
    ),

    projection_scale=10,

    lonaxis=dict(
        range=[72.4, 81.1]
    ),

    lataxis=dict(
        range=[15.3, 22.3]
    ),

    showland=False,

    showocean=False,

    showcountries=False
)


# --------------------------------------------------
# MAP LAYOUT
# --------------------------------------------------

fig.update_layout(

    height=700,

    margin=dict(
        l=0,
        r=0,
        t=20,
        b=0
    ),

    paper_bgcolor="white",

    plot_bgcolor="white",

    legend=dict(
        title="CCI Category",
        orientation="v",
        x=0.90,
        y=0.90
    )
)


# --------------------------------------------------
# DISPLAY MAP
# --------------------------------------------------

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "scrollZoom": True,
        "displayModeBar": True
    }
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
