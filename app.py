import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Maharashtra Climate Change Index",
    layout="wide"
)

st.title("Maharashtra Climate Change Index")
st.write("District-wise Climate Change Index for Maharashtra (2000–2025)")


# =========================================================
# 1. READ EXCEL FILE
# =========================================================

excel_file = "Maharashtra_36_Districts_PCA_CCI_Final_Ranking.xlsx"

df = pd.read_excel(
    excel_file,
    sheet_name="Final_CCI_Ranking"
)


# =========================================================
# 2. CHECK REQUIRED COLUMNS
# =========================================================

required_columns = [
    "District",
    "PCA_CCI",
    "Rank",
    "Rainfall_Score",
    "Tmax_Score",
    "Tmin_Score",
    "DTR_Score"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(
        "These columns are missing from the Excel file: "
        + ", ".join(missing_columns)
    )
    st.stop()


# =========================================================
# 3. CLEAN DISTRICT NAMES
# =========================================================

df["District"] = (
    df["District"]
    .astype(str)
    .str.strip()
)


# =========================================================
# 4. READ GEOJSON
# =========================================================

geojson_file = "Maharashtra_Districts_36.geojson"

with open(
    geojson_file,
    "r",
    encoding="utf-8"
) as f:

    geojson = json.load(f)


# =========================================================
# 5. NORMALIZE DISTRICT NAMES
# =========================================================

name_changes = {

    "Chhatrapati Sambhaji Nagar": "Aurangabad",
    "Chhatrapati Sambhajinagar": "Aurangabad",
    "Sambhajinagar": "Aurangabad",

    "Ahilyanagar": "Ahmednagar"

}


df["GeoDistrict"] = (
    df["District"]
    .replace(name_changes)
    .str.strip()
)


# =========================================================
# 6. CHECK GEOJSON DISTRICT NAMES
# =========================================================

geo_districts = []

for feature in geojson["features"]:

    district = feature["properties"].get("district")

    if district is not None:

        geo_districts.append(
            str(district).strip()
        )


# =========================================================
# 7. QUANTILE CLASSIFICATION
# =========================================================

q33 = df["PCA_CCI"].quantile(1 / 3)

q67 = df["PCA_CCI"].quantile(2 / 3)


def classify_cci(value):

    if value <= q33:
        return "Low"

    elif value <= q67:
        return "Moderate"

    else:
        return "High"


df["CCI_Category"] = df["PCA_CCI"].apply(
    classify_cci
)


# =========================================================
# 8. CREATE DISTRICT LABEL POSITIONS
# =========================================================

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

    district_name = (
        feature["properties"]
        .get("district")
    )

    geometry = feature.get("geometry")

    if geometry is None:
        continue

    coordinates = geometry.get(
        "coordinates"
    )

    if coordinates is None:
        continue

    points = get_all_points(
        coordinates
    )

    if len(points) > 0:

        avg_lon = (
            sum(point[0] for point in points)
            / len(points)
        )

        avg_lat = (
            sum(point[1] for point in points)
            / len(points)
        )

        label_data.append({

            "GeoDistrict": str(
                district_name
            ).strip(),

            "lon": avg_lon,

            "lat": avg_lat

        })


labels = pd.DataFrame(
    label_data
)


# =========================================================
# 9. ADD RANK TO LABEL DATA
# =========================================================

labels = labels.merge(

    df[
        [
            "GeoDistrict",
            "District",
            "Rank"
        ]
    ],

    on="GeoDistrict",

    how="left"

)


# =========================================================
# 10. CREATE MAP
# =========================================================

st.subheader(
    "Maharashtra District Climate Change Map"
)
fig = go.Figure()

# =========================================================
# 11. CATEGORY COLOURS
# =========================================================

category_colors = {

    "Low": "yellow",

    "Moderate": "orange",

    "High": "red",

}


# =========================================================
# 12. ADD THREE MAP LAYERS
# =========================================================

for category in [
    "Low",
    "Moderate",
    "High"
]:

    category_df = df[
        df["CCI_Category"] == category
    ].copy()


    # -----------------------------------------------------
    # Keep only GeoJSON features belonging to this category
    # -----------------------------------------------------

    category_names = set(
        category_df["GeoDistrict"]
    )


    category_features = []

    for feature in geojson["features"]:

        district = (
            feature["properties"]
            .get("district")
        )

        if district in category_names:

            category_features.append(
                feature
            )


    category_geojson = {

        "type": "FeatureCollection",

        "features": category_features

    }


    # -----------------------------------------------------
    # Add choropleth layer
    # -----------------------------------------------------

    fig.add_trace(

        go.Choropleth(

            geojson=category_geojson,

            locations=category_df[
                "GeoDistrict"
            ],

            z=[
                1
            ] * len(category_df),

            featureidkey="properties.district",

            colorscale=[
                [0, category_colors[category]],
                [1, category_colors[category]]
            ],

            showscale=False,

            name=category,

            marker_line_color="black",

            marker_line_width=1.3,

            customdata=category_df[
                [
                    "District",
                    "PCA_CCI",
                    "Rank"
                ]
            ].values,

            hovertemplate=(

                "<b>%{customdata[0]}</b>"
                "<br>PCA CCI: %{customdata[1]:.4f}"
                "<br>Rank: %{customdata[2]}"
                "<br>Category: "
                + category
                + "<extra></extra>"

            )

        )

    )


# =========================================================
# 13. ADD DISTRICT NAME + RANK
# =========================================================

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
            size=9,
            color="black"
        ),

        hoverinfo="text",

        hovertext=[

            f"{district}<br>Rank: {rank}"

            for district, rank

            in zip(
                labels["District"],
                labels["Rank"]
            )

        ],

        showlegend=False

    )

)


# =========================================================
# 14. MAP SETTINGS
# =========================================================

fig.update_geos(
    fitbounds="locations",
    visible=False,
    showcountries=False,
    showland=False,
    showcoastlines=False,
    showframe=False,
    projection_type="mercator"
)


# =========================================================
# 15. LAYOUT
# =========================================================

fig.update_layout(
    height=700,

    margin=dict(
        r=0,
        t=20,
        l=0,
        b=0
    ),

    paper_bgcolor="#E8E8E8",
    plot_bgcolor="#E8E8E8",

    legend=dict(
        title="CCI Category",
        orientation="v",
        yanchor="top",
        y=0.98,
        xanchor="right",
        x=0.98,
        bgcolor="white",
        bordercolor="black",
        borderwidth=1
    )
)
# =========================================================
# 16. DISPLAY MAP
# =========================================================

st.plotly_chart(

    fig,

    use_container_width=True

)


# =========================================================
# 17. CATEGORY SUMMARY
# =========================================================

st.subheader(
    "CCI Category Summary"
)


low_count = (
    df["CCI_Category"] == "Low"
).sum()


moderate_count = (
    df["CCI_Category"] == "Moderate"
).sum()


high_count = (
    df["CCI_Category"] == "High"
).sum()


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "Low",
        low_count
    )


with col2:

    st.metric(
        "Moderate",
        moderate_count
    )


with col3:

    st.metric(
        "High",
        high_count
    )


# =========================================================
# 18. CLASSIFICATION THRESHOLDS
# =========================================================

st.subheader(
    "PCA Climate Change Index Classification"
)


st.write(
    f"33.33rd Percentile: {q33:.4f}"
)


st.write(
    f"66.67th Percentile: {q67:.4f}"
)


st.write(
    f"🟡 Low: PCA_CCI ≤ {q33:.4f}"
)


st.write(
    f"🟠 Moderate: {q33:.4f} < PCA_CCI ≤ {q67:.4f}"
)


st.write(
    f"🔴 High: PCA_CCI > {q67:.4f}"
)


# =========================================================
# 19. RANKING TABLE
# =========================================================

st.subheader(
    "CCI Ranking"
)


display_columns = [

    "District",

    "PCA_CCI",

    "Rank",

    "Rainfall_Score",

    "Tmax_Score",

    "Tmin_Score",

    "DTR_Score",

    "CCI_Category"

]


st.dataframe(

    df[
        display_columns
    ].sort_values(
        "Rank"
    ),

    use_container_width=True

)


# =========================================================
# 20. DOWNLOAD CSV
# =========================================================

csv_data = df[
    display_columns
].sort_values(
    "Rank"
).to_csv(
    index=False
)


st.download_button(

    label="Download CCI Ranking (CSV)",

    data=csv_data,

    file_name="Maharashtra_CCI_Ranking.csv",

    mime="text/csv"

)


# =========================================================
# 21. DOWNLOAD MAP AS PNG
# =========================================================

st.subheader(
    "Download Map"
)


try:

    png_bytes = fig.to_image(
        format="png",
        width=1400,
        height=900,
        scale=2
    )


    st.download_button(

        label="Download Maharashtra CCI Map (PNG)",

        data=png_bytes,

        file_name="Maharashtra_CCI_Map.png",

        mime="image/png"

    )

except Exception:

    st.info(
        "PNG download requires the kaleido package. "
        "Add kaleido to requirements.txt and redeploy."
    )
