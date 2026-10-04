import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go


# ==================================================
# PAGE SETTINGS
# ==================================================

st.set_page_config(
    page_title="Maharashtra Climate Change Index",
    layout="wide"
)


# ==================================================
# TITLE
# ==================================================

st.title("Maharashtra District CCI Map")

st.write(
    "District-wise Climate Change Index for Maharashtra (2000–2025)"
)


# ==================================================
# READ CCI DATA
# ==================================================

cci = pd.read_excel(
    "Maharashtra_36_Districts_PCA_CCI_Final_Ranking.xlsx",
    sheet_name="Final_CCI_Ranking"
)

cci["District"] = (
    cci["District"]
    .astype(str)
    .str.strip()
)


# ==================================================
# MATCH DISTRICT NAMES WITH GEOJSON
# ==================================================

name_changes = {
    "Chhatrapati Sambhaji Nagar": "Aurangabad",
    "Chhatrapati Sambhajinagar": "Aurangabad",
    "Sambhajinagar": "Aurangabad",
    "Ahilyanagar": "Ahmednagar"
}

cci["GeoDistrict"] = (
    cci["District"].replace(name_changes)
)


# ==================================================
# LOW / MODERATE / HIGH CLASSIFICATION
# ==================================================

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


# ==================================================
# READ GEOJSON
# ==================================================

with open(
    "Maharashtra_Districts_36.geojson",
    "r",
    encoding="utf-8"
) as f:

    geojson = json.load(f)


# ==================================================
# CREATE MAP
# ==================================================

fig = go.Figure()


# ==================================================
# CATEGORY COLOURS
# ==================================================

category_colors = {
    "Low": "yellow",
    "Moderate": "orange",
    "High": "red"
}


# ==================================================
# ADD DISTRICT POLYGONS
# ==================================================

for category in ["Low", "Moderate", "High"]:

    data = cci[
        cci["CCI_Category"] == category
    ].copy()

    if len(data) == 0:
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


# ==================================================
# FIND DISTRICT LABEL POSITIONS
# ==================================================

label_data = []


def get_points(obj):

    points = []

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
                points.extend(
                    get_points(item)
                )

    return points


for feature in geojson["features"]:

    district = feature["properties"].get(
        "district"
    )

    geometry = feature.get("geometry")

    if geometry is None:
        continue

    points = get_points(
        geometry.get("coordinates")
    )

    if not points:
        continue

    lon = (
        sum(p[0] for p in points)
        / len(points)
    )

    lat = (
        sum(p[1] for p in points)
        / len(points)
    )

    label_data.append(
        {
            "GeoDistrict": district,
            "lon": lon,
            "lat": lat
        }
    )


labels = pd.DataFrame(label_data)


# ==================================================
# MATCH LABELS WITH CCI DATA
# ==================================================

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


# Keep only districts having CCI data
labels = labels.dropna(
    subset=["Rank"]
).copy()


# ==================================================
# ADD DISTRICT NAME + RANK
# ==================================================

fig.add_trace(
    go.Scattergeo(

        lon=labels["lon"],

        lat=labels["lat"],

        text=[
            f"{district}<br>Rank: {int(rank)}"
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


# ==================================================
# MAHARASHTRA ONLY — ZOOMED IN
# ==================================================

fig.update_geos(

    visible=False,

    projection_type="mercator",

    center=dict(
        lat=19.2,
        lon=76.5
    ),

    projection_scale=6.5,

    lonaxis=dict(
        range=[
            72.4,
            81.2
        ]
    ),

    lataxis=dict(
        range=[
            15.3,
            22.3
        ]
    ),

    showland=False,

    showocean=False,

    showcountries=False,

    showcoastlines=False,

    showframe=False
)


# ==================================================
# MAP LAYOUT + LEGEND
# ==================================================

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

        x=0.88,

        y=0.90,

        bgcolor="white",

        bordercolor="black",

        borderwidth=1
    )
)


# ==================================================
# DISPLAY MAP
# ==================================================

st.plotly_chart(
    fig,

    use_container_width=True,

    config={
        "scrollZoom": True,
        "displayModeBar": True,
        "displaylogo": False
    }
)


# ==================================================
# DOWNLOAD MAP AS PNG
# ==================================================

st.subheader("Download Map")

try:

    image_bytes = fig.to_image(
        format="png",
        width=1600,
        height=1000,
        scale=2
    )

    st.download_button(
        label="Download Map as PNG",

        data=image_bytes,

        file_name="Maharashtra_CCI_Map.png",

        mime="image/png"
    )

except Exception:

    st.warning(
        "PNG download requires Kaleido. "
        "Add 'kaleido' to requirements.txt and redeploy the app."
    )


# ==================================================
# CATEGORY SUMMARY
# ==================================================

st.subheader("CCI Category Summary")

category_summary = (
    cci["CCI_Category"]
    .value_counts()
    .reindex(
        [
            "Low",
            "Moderate",
            "High"
        ],
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


# ==================================================
# CCI RANKING
# ==================================================

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


# ==================================================
# DOWNLOAD CCI RANKING
# ==================================================

csv_data = cci.to_csv(
    index=False
)

st.download_button(

    label="Download CCI Ranking (CSV)",

    data=csv_data,

    file_name="Maharashtra_CCI_Ranking.csv",

    mime="text/csv"
)
