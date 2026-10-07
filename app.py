
import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from shapely.geometry import shape

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
try:
    with open(
        geojson_file,
        "r",
        encoding="utf-8"
    ) as f:
        geojson = json.load(f)
except Exception as e:
    st.error(f"Could not find or read {geojson_file}. Please run the previous notebook cells to build it first. Error: {e}")
    st.stop()

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

df["CCI_Category"] = df["PCA_CCI"].apply(classify_cci)

# =========================================================
# 8. CREATE DISTRICT LABEL POSITIONS
# =========================================================
label_data = []
for feature in geojson["features"]:
    district_name = str(feature["properties"].get("district")).strip()
    geometry = feature.get("geometry")
    if geometry is None:
        continue
    polygon = shape(geometry)
    point = polygon.representative_point()
    label_data.append({
        "GeoDistrict": district_name,
        "lon": point.x,
        "lat": point.y
    })

labels = pd.DataFrame(label_data)

# =========================================================
# 9. ADD RANK TO LABEL DATA
# =========================================================
labels = labels.merge(
    df[["GeoDistrict", "District", "Rank"]],
    on="GeoDistrict",
    how="left"
)

# =========================================================
# 10. CREATE MAP
# =========================================================
st.subheader("Maharashtra District Climate Change Map")
fig = go.Figure()

category_colors = {
    "Low": "#FFFF80",       # Soft, clean yellow
    "Moderate": "#FFA500",  # Vibrant orange
    "High": "#FF4D4D",      # Warning red
}

# Calculate center of Maharashtra dynamically to center our mapbox
mean_lat = labels["lat"].mean() if not labels.empty else 19.7
mean_lon = labels["lon"].mean() if not labels.empty else 75.7

# =========================================================
# 12. ADD THREE MAP LAYERS USING CHOROPLETHMAPBOX
# =========================================================
for category in ["Low", "Moderate", "High"]:
    category_df = df[df["CCI_Category"] == category].copy()
    category_names = set(category_df["GeoDistrict"])
    category_features = []

    for feature in geojson["features"]:
        district = feature["properties"].get("district")
        if district in category_names:
            category_features.append(feature)

    category_geojson = {
        "type": "FeatureCollection",
        "features": category_features
    }

    fig.add_trace(
        go.Choroplethmapbox(
            geojson=category_geojson,
            locations=category_df["GeoDistrict"],
            z=[0] * len(category_df),
            featureidkey="properties.district",
            zmin=0,
            zmax=1,
            colorscale=[
                [0, category_colors[category]],
                [1, category_colors[category]]
            ],
            showscale=False,
            name=category,
            showlegend=True,
            marker_opacity=0.85,
            marker_line_color="black",
            marker_line_width=1.5,
            customdata=category_df[["District", "PCA_CCI", "Rank"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b>"
                "<br>PCA CCI: %{customdata[1]:.4f}"
                "<br>Rank: %{customdata[2]}"
                "<br>Category: " + category + "<extra></extra>"
            )
        )
    )

# =========================================================
# 13. ADD DISTRICT NAME + RANK USING SCATTERMAPBOX
# =========================================================
fig.add_trace(
    go.Scattermapbox(
        lon=labels["lon"],
        lat=labels["lat"],
        text=[
            f"{district}<br>Rank: {rank}"
            for district, rank in zip(labels["District"], labels["Rank"])
        ],
        mode="text",
        textfont=dict(size=10, color="black", weight="bold"),
        hoverinfo="text",
        hovertext=[
            f"{district}<br>Rank: {rank}"
            for district, rank in zip(labels["District"], labels["Rank"])
        ],
        showlegend=False
    )
)

# =========================================================
# 14. MAP SETTINGS WITH MAPBOX STYLE
# =========================================================
fig.update_layout(
    mapbox=dict(
        style="open-street-map",
        center=dict(lat=mean_lat, lon=mean_lon),
        zoom=6.0
    ),
    height=800,
    margin=dict(r=10, t=20, l=10, b=10),
    paper_bgcolor="white",
    plot_bgcolor="white",
    legend=dict(
        title="CCI Category",
        orientation="v",
        yanchor="top",
        y=0.98,
        xanchor="left",
        x=0.01
    )
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "scrollZoom": True,
        "displayModeBar": True
    }
)

# =========================================================
# 17. CATEGORY SUMMARY
# =========================================================
st.subheader("CCI Category Summary")
low_count = (df["CCI_Category"] == "Low").sum()
moderate_count = (df["CCI_Category"] == "Moderate").sum()
high_count = (df["CCI_Category"] == "High").sum()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Low", low_count)
with col2:
    st.metric("Moderate", moderate_count)
with col3:
    st.metric("High", high_count)

# =========================================================
# 18. CLASSIFICATION THRESHOLDS
# =========================================================
st.subheader("PCA Climate Change Index Classification")
st.write(f"33.33rd Percentile: {q33:.4f}")
st.write(f"66.67th Percentile: {q67:.4f}")
st.write(f"🟡 Low: PCA_CCI ≤ {q33:.4f}")
st.write(f"🟠 Moderate: {q33:.4f} < PCA_CCI ≤ {q67:.4f}")
st.write(f"🔴 High: PCA_CCI > {q67:.4f}")

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
    # Using the standard modern mapbox-to-image engine
    png_bytes = fig.to_image(format="png", width=1400, height=900, scale=2)
    st.download_button(
        label="Download Maharashtra CCI Map (PNG)",
        data=png_bytes,
        file_name="Maharashtra_CCI_Map.png",
        mime="image/png"
    )
except Exception as e:
    st.info("PNG download requires the kaleido package.")
