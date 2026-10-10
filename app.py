
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Maharashtra Climate Change Index",
    page_icon="🌦️",
    layout="wide"
)

# ==========================================
# 2. PROJECT TITLE
# ==========================================
st.title("🌦️ Maharashtra Climate Change Index")
st.subheadar("District-wise Climate Change Index for Maharashtra (2000–2025)")

# =========================================================
# 1. READ EXCEL FILE
# =========================================================
excel_file = "Maharashtra_36_Districts_PCA_CCI_Final_Ranking.xlsx"
try:
    df = pd.read_excel(
        excel_file,
        sheet_name="Final_CCI_Ranking"
    )
except Exception as e:
    st.error(f"Could not find or read {excel_file}. Please ensure you upload this file to Colab. Error: {e}")
    st.stop()
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
# ==========================================
# 4. DISPLAY RANKING RESULTS
# ==========================================
if ranking is not None:

    required_columns = ["Rank", "District", "PCA_CCI"]

    if all(col in ranking.columns for col in required_columns):

        ranking = ranking[required_columns].copy()

        ranking["Rank"] = pd.to_numeric(
            ranking["Rank"], errors="coerce"
        )
        ranking["PCA_CCI"] = pd.to_numeric(
            ranking["PCA_CCI"], errors="coerce"
        )

        ranking = ranking.dropna(
            subset=["Rank", "District", "PCA_CCI"]
        )

        ranking["Rank"] = ranking["Rank"].astype(int)
        ranking = ranking.sort_values("Rank")

        st.success("Climate index ranking loaded successfully!")

        # Summary metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Districts Included",
                ranking["District"].nunique()
            )

        with col2:
            st.metric(
                "Highest PCA CCI",
                f"{ranking['PCA_CCI'].max():.4f}"
            )

        with col3:
            st.metric(
                "Lowest PCA CCI",
                f"{ranking['PCA_CCI'].min():.4f}"
            )

        st.divider()

        # Ranking table
        st.header("District-Wise CCI Ranking")

        st.dataframe(
            ranking,
            use_container_width=True,
            hide_index=True
        )

        # Bar chart
        st.header("Compare Districts")

        chart_data = ranking.sort_values(
            "PCA_CCI", ascending=False
        )

        fig = px.bar(
            chart_data,
            x="District",
            y="PCA_CCI",
            hover_data=["Rank"],
            title="PCA-Based Climate Change Index by District",
            labels={
                "District": "District",
                "PCA_CCI": "PCA-Based CCI"
            }
        )

        fig.update_layout(
            xaxis_tickangle=-60,
            height=600
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # Download results
        st.download_button(
            label="Download CCI Ranking CSV",
            data=ranking.to_csv(index=False).encode("utf-8"),
            file_name="Maharashtra_CCI_Ranking.csv",
            mime="text/csv"
        )

    else:
        st.error(
            "The CSV must contain these columns: "
            "Rank, District, PCA_CCI. "
            f"Columns found: {list(ranking.columns)}"
        )

else:
    st.warning(
        "CCI_Ranking.csv was not found. "
        "Upload it using the sidebar or add it "
        "to the GitHub repository."
    )

# ==========================================
# 5. MAHARASHTRA DISTRICT MAP
# ==========================================
st.divider()
st.header("Maharashtra Climate Change Index Map")

geojson_path = Path("Maharashtra_CCI_Map.geojson")

if geojson_path.exists():

    try:
        with open(
            geojson_path, "r", encoding="utf-8"
        ) as file:
            geojson_data = json.load(file)

        features = geojson_data.get("features", [])

        # Read district attributes from GeoJSON
        map_df = pd.DataFrame([
            feature.get("properties", {})
            for feature in features
        ])

        required_map_columns = [
            "Map_District",
            "District",
            "Rank",
            "PCA_CCI",
            "Category"
        ]

        if not all(
            col in map_df.columns
            for col in required_map_columns
        ):
            st.error(
                "The GeoJSON file is missing required columns. "
                "Please check Map_District, District, Rank, "
                "PCA_CCI, and Category."
            )

        else:
            map_df["PCA_CCI"] = pd.to_numeric(
                map_df["PCA_CCI"], errors="coerce"
            )
            map_df["Rank"] = pd.to_numeric(
                map_df["Rank"], errors="coerce"
            )

            map_df = map_df.dropna(
                subset=[
                    "Map_District",
                    "District",
                    "Rank",
                    "PCA_CCI"
                ]
            ).copy()

            # Ensure feature identifiers are strings
            map_df["Map_District"] = (
                map_df["Map_District"].astype(str)
            )

            for feature in features:
                props = feature.get("properties", {})
                if "Map_District" in props:
                    props["Map_District"] = str(
                        props["Map_District"]
                    )

            # Build the district choropleth map
            fig_map = px.choropleth(
                map_df,
                geojson=geojson_data,
                locations="Map_District",
                featureidkey="properties.Map_District",
                color="PCA_CCI",
                hover_name="District",
                hover_data={
                    "Rank": True,
                    "PCA_CCI": ":.2f",
                    "Category": True,
                    "Map_District": False
                },
                color_continuous_scale="YlOrRd",
                projection="mercator",
                title="District-wise Climate Change Index"
            )

            # Fit the geographic view to the district shapes
            fig_map.update_geos(
                fitbounds="locations",
                visible=False
            )

            # Add district names using geographic label points.
            # For polygons, use the mean of their exterior vertices
            # as an approximate label position.
            label_lons = []
            label_lats = []
            label_names = []

            for feature in features:
                props = feature.get("properties", {})
                district_name = props.get("District")

                if not district_name:
                    district_name = props.get("Map_District")

                geometry = feature.get("geometry", {})
                geom_type = geometry.get("type")
                coords = geometry.get("coordinates", [])

                # Handle Polygon and MultiPolygon geometries
                polygons = []

                if geom_type == "Polygon":
                    polygons = [coords]
                elif geom_type == "MultiPolygon":
                    polygons = coords

                # Use the largest exterior ring for label position
                best_ring = None
                best_size = 0

                for polygon in polygons:
                    if polygon and polygon[0]:
                        ring = polygon[0]
                        if len(ring) > best_size:
                            best_ring = ring
                            best_size = len(ring)

                if best_ring and district_name:
                    lon = sum(point[0] for point in best_ring) / len(best_ring)
                    lat = sum(point[1] for point in best_ring) / len(best_ring)

                    label_lons.append(lon)
                    label_lats.append(lat)
                    label_names.append(str(district_name))

            # Overlay labels on the map
            if label_names:
                fig_map.add_trace(
                    go.Scattergeo(
                        lon=label_lons,
                        lat=label_lats,
                        text=label_names,
                        mode="text",
                        textfont=dict(
                            size=8,
                            color="black"
                        ),
                        hoverinfo="skip",
                        showlegend=False
                    )
                )

            fig_map.update_layout(
                height=750,
                margin=dict(
                    l=10, r=10, t=60, b=10
                ),
                coloraxis_colorbar=dict(
                    title="PCA CCI"
                )
            )

            st.plotly_chart(
                fig_map,
                use_container_width=True
            )

            st.caption(
                "District colors represent PCA CCI scores. "
                "Hover over a district to see its score, "
                "rank, and category. Text labels identify districts."
            )

    except Exception as error:
        st.error(
            f"Unable to display the district map: {error}"
        )

else:
    st.warning(
        "Maharashtra_CCI_Map.geojson was not found. "
        "Upload this file to the same GitHub folder as app.py."
    )

# =========================================================
# 19. RANKING TABLE
# =========================================================
st.subheader("CCI Ranking")
display_columns = [
    "District", "PCA_CCI", "Rank", "Rainfall_Score",
    "Tmax_Score", "Tmin_Score", "DTR_Score", "CCI_Category"
]

st.dataframe(
    df[display_columns].sort_values("Rank"),
    use_container_width=True
)

# =========================================================
# 20. DOWNLOAD CSV
# =========================================================
csv_data = df[display_columns].sort_values("Rank").to_csv(index=False)
st.download_button(
    label="Download CCI Ranking (CSV)",
    data=csv_data,
    file_name="Maharashtra_CCI_Ranking.csv",
    mime="text/csv"
)

# =========================================================
# 21. DOWNLOAD MAP AS PNG
# =========================================================
st.subheader("Download Map")
try:
    png_bytes = fig.to_image(format="png", width=1400, height=900, scale=2)
    st.download_button(
        label="Download Maharashtra CCI Map (PNG)",
        data=png_bytes,
        file_name="Maharashtra_CCI_Map.png",
        mime="image/png"
    )
except Exception as e:
    st.info("PNG download requires the kaleido package.")
