import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Maharashtra Climate Change Index",
    layout="wide"
)

st.title("Maharashtra District Climate Change Index")
st.write("District-wise Climate Change Index for Maharashtra (2000–2025)")


# --------------------------------------------------
# 1. READ EXCEL
# --------------------------------------------------

df = pd.read_excel(
    "Maharashtra_36_Districts_PCA_CCI_Final_Ranking.xlsx",
    sheet_name="Final_CCI_Ranking"
)

df["District"] = df["District"].astype(str).str.strip()


# --------------------------------------------------
# 2. READ GEOJSON
# --------------------------------------------------

with open(
    "Maharashtra_Districts_36.geojson",
    "r",
    encoding="utf-8"
) as f:
    geojson = json.load(f)


# --------------------------------------------------
# 3. DISTRICT NAME MATCHING
# --------------------------------------------------

name_changes = {
    "Chhatrapati Sambhaji Nagar": "Aurangabad",
    "Chhatrapati Sambhajinagar": "Aurangabad",
    "Sambhajinagar": "Aurangabad",
    "Ahilyanagar": "Ahmednagar"
}

df["GeoDistrict"] = df["District"].replace(name_changes)


# --------------------------------------------------
# 4. CCI CLASSIFICATION
# --------------------------------------------------

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


# --------------------------------------------------
# 5. DISTRICT LABEL POSITIONS
# --------------------------------------------------

def get_all_points(coords):

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

    extract(coords)

    return points


label_data = []

for feature in geojson["features"]:

    district_name = feature["properties"].get("district")

    geometry = feature["geometry"]

    points = get_all_points(
        geometry["coordinates"]
    )

    if points:

        avg_lon = (
            sum(p[0] for p in points)
            / len(points)
        )

        avg_lat = (
            sum(p[1] for p in points)
            / len(points)
        )

        label_data.append({

            "District": district_name,

            "lon": avg_lon,

            "lat": avg_lat

        })


labels = pd.DataFrame(label_data)


# --------------------------------------------------
# 6. MATCH RANK WITH DISTRICT
# --------------------------------------------------

labels = labels.merge(

    df[
        [
            "GeoDistrict",
            "District",
            "Rank"
        ]
    ],

    left_on="District",

    right_on="GeoDistrict",

    how="left"
)


# --------------------------------------------------
# 7. CHOROPLETH MAP
# --------------------------------------------------

st.subheader("Maharashtra District Climate Change Index Map")


fig = px.choropleth(

    df,

    geojson=geojson,

    locations="GeoDistrict",

    featureidkey="properties.district",

    color="PCA_CCI",

    hover_name="District",

    hover_data={

        "PCA_CCI": ":.4f",

        "Rank": True,

        "CCI_Category": True

    },

    color_continuous_scale="YlOrRd"

)


# --------------------------------------------------
# 8. PERMANENT DISTRICT NAME + RANK LABEL
# --------------------------------------------------

fig.add_trace(

    go.Scattergeo(

        lon=labels["lon"],

        lat=labels["lat"],

        text=[

            f"{name}<br>Rank: {rank}"

            for name, rank in zip(

                labels["District_y"],

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

                labels["District_y"],

                labels["Rank"]

            )

        ],

        showlegend=False

    )

)


# --------------------------------------------------
# 9. MAP SETTINGS
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
# 10. RESULT TABLE
# --------------------------------------------------

st.subheader("District Climate Change Index Result")


st.dataframe(

    df[

        [

            "District",

            "PCA_CCI",

            "Rank",

            "CCI_Category",

            "Rainfall_Score",

            "Tmax_Score",

            "Tmin_Score",

            "DTR_Score"

        ]

    ],

    use_container_width=True

)


# --------------------------------------------------
# 11. CCI CLASSIFICATION
# --------------------------------------------------

st.subheader(
    "PCA Climate Change Index Classification"
)

st.write(
    f"33.33rd Percentile: {q33:.2f}"
)

st.write(
    f"66.67th Percentile: {q67:.2f}"
)

st.write(
    f"🟡 Low: PCA_CCI ≤ {q33:.2f}"
)

st.write(
    f"🟠 Moderate: {q33:.2f} < PCA_CCI ≤ {q67:.2f}"
)

st.write(
    f"🔴 High: PCA_CCI > {q67:.2f}"
)


# --------------------------------------------------
# 12. CATEGORY SUMMARY
# --------------------------------------------------

st.subheader("CCI Category Summary")


category_summary = (

    df["CCI_Category"]

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

    use_container_width=True

)


# --------------------------------------------------
# 13. DOWNLOAD CCI RANKING
# --------------------------------------------------

csv_data = df.to_csv(
    index=False
)


st.download_button(

    label="Download CCI Ranking (CSV)",

    data=csv_data,

    file_name="Maharashtra_CCI_Ranking.csv",

    mime="text/csv"

)
