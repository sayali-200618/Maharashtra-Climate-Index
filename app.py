# ============================================================
# MAHARASHTRA CLIMATE CHANGE INDEX (CCI)
# PCA-BASED DISTRICT ANALYSIS AND INTERACTIVE DASHBOARD
# Streamlit Application
#
# Map categories:
# Q1 - Highest CCI
# Q2 - Medium CCI
# Q3 - Lowest CCI
#
# IMPORTANT:
# Keep this file in the same folder as CCI_Ranking.csv and,
# optionally, one of the supported Maharashtra GeoJSON files.
# ============================================================

import io
import re
import tempfile
import unicodedata
import zipfile
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="District-wise Climate Change Index of Maharashtra",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 2. PROJECT PATHS AND CONSTANTS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

RANKING_FILE = BASE_DIR / "CCI_Ranking.csv"

MAP_CANDIDATES = [
    BASE_DIR / "Maharashtra_District_Boundaries.geojson",
    BASE_DIR / "Maharashtra_CCI_Map.geojson",
    BASE_DIR / "Maharashtra.geojson",
]

MAP_URL = (
    "https://gist.githubusercontent.com/"
    "saketkc/7c1ce9d993773ced9974f6c57730b7df/"
    "raw/Maharashtra.geojson"
)

CCI_COLORS = {
    "Q1 - Highest CCI": "#8B0000",
    "Q2 - Medium CCI": "#FDBB84",
    "Q3 - Lowest CCI": "#FFF2AE",
}

CCI_GROUPS = list(CCI_COLORS.keys())

# ============================================================
# 4. DISTRICT NAME NORMALIZATION
# ============================================================

def normalize_district_name(value):
    """
    Normalize district names for matching the ranking CSV
    with the GeoJSON boundary file.

    Mumbai City and Mumbai Suburban are deliberately kept
    as two separate districts.
    """

    if pd.isna(value):
        return ""

    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(
        char for char in value
        if not unicodedata.combining(char)
    )

    value = value.strip().lower()
    value = re.sub(r"\bdistrict\b", "", value)
    value = re.sub(r"[^a-z0-9]", "", value)

    aliases = {
        "aurangabad": "chhatrapatisambhajinagar",
        "chhatrapatisambhajinagar": "chhatrapatisambhajinagar",

        "osmanabad": "dharashiv",
        "dharashiv": "dharashiv",

        "ahmednagar": "ahilyanagar",
        "ahmadnagar": "ahilyanagar",
        "ahilyanagar": "ahilyanagar",

        "raigarh": "raigad",
        "raigad": "raigad",

        "bombay": "mumbaicity",
        "mumbai": "mumbaicity",
        "mumbaicity": "mumbaicity",
        "mumbaicitydistrict": "mumbaicity",

        "mumbaisuburban": "mumbaisuburban",
        "mumbaisuburb": "mumbaisuburban",
    }

    return aliases.get(value, value)


def find_column(data, candidates):
    """Find a column using case-insensitive normalized names."""

    lookup = {
        re.sub(r"[^a-z0-9]", "", str(col).strip().lower()): col
        for col in data.columns
    }

    for candidate in candidates:
        key = re.sub(
            r"[^a-z0-9]",
            "",
            str(candidate).strip().lower(),
        )

        if key in lookup:
            return lookup[key]

    return None


DISTRICT_CANDIDATES = [
    "District",
    "District_Name",
    "District Name",
    "district_name",
    "DISTRICT",
    "DIST_NAME",
    "dtname",
    "DTNAME",
    "NAME_2",
    "name_2",
    "name",
]

SCORE_CANDIDATES = [
    "PCA_CCI",
    "PCA CCI",
    "CCI",
    "CCI_Score",
    "CCI Score",
]

RANK_CANDIDATES = [
    "Rank",
    "CCI_Rank",
    "CCI Rank",
    "Overall_Rank",
    "Overall Rank",
    "Final_Rank",
    "Final Rank",
]


# ============================================================
# 5. LOAD AND PREPARE CCI RANKING DATA
# ============================================================

def prepare_ranking(data):
    """
    Validate ranking data, calculate rank where a CCI score
    is available, and assign Q1/Q2/Q3 by ranking position.

    Rank 1 = highest CCI.
    """

    if data is None or data.empty:
        raise ValueError("The ranking file is empty.")

    data = data.copy()
    data.columns = [str(col).strip() for col in data.columns]

    district_col = find_column(
        data,
        DISTRICT_CANDIDATES,
    )

    score_col = find_column(
        data,
        SCORE_CANDIDATES,
    )

    rank_col = find_column(
        data,
        RANK_CANDIDATES,
    )

    if district_col is None:
        raise ValueError(
            "The ranking file must contain a District column."
        )

    if score_col is None and rank_col is None:
        raise ValueError(
            "The ranking file must contain PCA_CCI or Rank."
        )

    result = pd.DataFrame()

    result["District"] = (
        data[district_col]
        .astype(str)
        .str.strip()
    )

    if score_col is not None:
        result["PCA_CCI"] = pd.to_numeric(
            data[score_col],
            errors="coerce",
        )
    else:
        result["PCA_CCI"] = np.nan

    if rank_col is not None:
        result["Rank"] = pd.to_numeric(
            data[rank_col],
            errors="coerce",
        )
    else:
        result["Rank"] = np.nan

    result = result.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    result = result[
        result["District"].notna()
        & result["District"].ne("")
        & result["District"].str.lower().ne("nan")
    ].copy()

    if score_col is not None:
        result = result.dropna(
            subset=["PCA_CCI"]
        ).copy()

        result = result.sort_values(
            "PCA_CCI",
            ascending=False,
        ).reset_index(drop=True)

        result["Rank"] = np.arange(
            1,
            len(result) + 1,
        )

    else:
        result = result.dropna(
            subset=["Rank"]
        ).copy()

        result = result.sort_values(
            "Rank",
            ascending=True,
        ).reset_index(drop=True)

        # Convert the supplied rank order to consecutive positions.
        result["Rank"] = np.arange(
            1,
            len(result) + 1,
        )

    if result.empty:
        raise ValueError(
            "No valid ranking records were found."
        )

    result["Map_Key"] = result["District"].apply(
        normalize_district_name
    )

    if result["Map_Key"].eq("").any():
        raise ValueError(
            "One or more district names are blank."
        )

    if result["Map_Key"].duplicated().any():
        duplicates = result.loc[
            result["Map_Key"].duplicated(keep=False),
            "District",
        ].tolist()

        raise ValueError(
            "Duplicate district names found after normalization: "
            f"{duplicates}"
        )

    # Divide the ordered district ranks into three approximately
    # equal groups. For 36 districts: 12 districts per group.
    number_of_districts = len(result)

    result["Rank_Position"] = np.arange(
        1,
        number_of_districts + 1,
    )

    result["CCI_Group"] = pd.cut(
        result["Rank_Position"],
        bins=[
            0,
            number_of_districts / 3,
            2 * number_of_districts / 3,
            number_of_districts,
        ],
        labels=CCI_GROUPS,
        include_lowest=True,
    )

    result["CCI_Group"] = result["CCI_Group"].astype(str)

    return result


@st.cache_data(show_spinner=False)
def read_ranking_csv(file_bytes):
    return pd.read_csv(io.BytesIO(file_bytes))


@st.cache_data(show_spinner=False)
def read_ranking_excel(file_bytes):
    return pd.read_excel(io.BytesIO(file_bytes), sheet_name=0)


# ============================================================
# 6. LOAD DISTRICT BOUNDARY FILE
# ============================================================

def read_boundary_file(uploaded_file):
    """
    Read GeoJSON, JSON, zipped Shapefile or GeoPackage.

    ZIP extraction is performed in a temporary directory.
    """

    if uploaded_file is None:
        return None

    filename = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_path = Path(temp_dir)

        if filename.endswith(".zip"):

            zip_path = temp_path / "boundaries.zip"
            zip_path.write_bytes(file_bytes)

            try:
                with zipfile.ZipFile(
                    zip_path,
                    "r",
                ) as archive:
                    archive.extractall(temp_path)

            except zipfile.BadZipFile as exc:
                raise ValueError(
                    "The uploaded ZIP file is invalid."
                ) from exc

            shp_files = list(
                temp_path.rglob("*.shp")
            )

            geojson_files = list(
                temp_path.rglob("*.geojson")
            )

            json_files = list(
                temp_path.rglob("*.json")
            )

            gpkg_files = list(
                temp_path.rglob("*.gpkg")
            )

            if shp_files:
                return gpd.read_file(shp_files[0])

            if geojson_files:
                return gpd.read_file(geojson_files[0])

            if json_files:
                return gpd.read_file(json_files[0])

            if gpkg_files:
                return gpd.read_file(gpkg_files[0])

            raise ValueError(
                "The ZIP file contains no supported boundary file."
            )

        suffix = Path(filename).suffix

        local_path = temp_path / (
            "boundaries" + suffix
        )

        local_path.write_bytes(file_bytes)

        if suffix in [
            ".geojson",
            ".json",
            ".gpkg",
            ".shp",
        ]:
            return gpd.read_file(local_path)

        raise ValueError(
            "Unsupported boundary format. "
            "Upload GeoJSON, JSON, ZIP Shapefile or GeoPackage."
        )


@st.cache_data(show_spinner=False)
def read_geojson_path(path_string, modified_time):
    return gpd.read_file(path_string)


# ============================================================
# 7. MERGE DISTRICT BOUNDARIES WITH CCI RANKING
# ============================================================

def merge_cci_map(boundaries, ranking):
    """
    Merge boundary polygons with the existing ranking data.

    IMPORTANT:
    - Uses the original CCI_Group column.
    - Does not create Group 1, Group 2 or Group 3.
    - Does not create an Unranked category.
    - Removes possible old Rank/CCI columns from GeoJSON
      before merging to prevent Rank_x and Rank_y conflicts.
    """

    if boundaries is None or boundaries.empty:
        raise ValueError(
            "The district boundary file is empty."
        )

    if ranking is None or ranking.empty:
        raise ValueError(
            "The CCI ranking data is empty."
        )

    boundaries = boundaries.copy()
    ranking_data = ranking.copy()

    if boundaries.geometry.name not in boundaries.columns:
        raise ValueError(
            "The boundary file does not contain geometry."
        )

    boundary_col = find_column(
        boundaries,
        DISTRICT_CANDIDATES,
    )

    ranking_col = find_column(
        ranking_data,
        DISTRICT_CANDIDATES,
    )

    if boundary_col is None:
        raise ValueError(
            "District-name column not found in GeoJSON. "
            f"Available columns: {list(boundaries.columns)}"
        )

    if ranking_col is None:
        raise ValueError(
            "District-name column not found in ranking data. "
            f"Available columns: {list(ranking_data.columns)}"
        )

    # The ranking preparation function should already create
    # these fields. Validate them before attempting the merge.
    required_ranking_columns = [
        "Rank",
        "PCA_CCI",
        "CCI_Group",
    ]

    missing = [
        col for col in required_ranking_columns
        if col not in ranking_data.columns
    ]

    if missing:
        raise ValueError(
            f"Ranking data is missing columns: {missing}. "
            f"Available columns: {list(ranking_data.columns)}"
        )

    # Create matching district keys.
    boundaries["_district_key"] = (
        boundaries[boundary_col]
        .apply(normalize_district_name)
    )

    ranking_data["_district_key"] = (
        ranking_data[ranking_col]
        .apply(normalize_district_name)
    )

    # Check duplicate keys before merging.
    if boundaries["_district_key"].duplicated().any():
        duplicates = boundaries.loc[
            boundaries["_district_key"].duplicated(keep=False),
            boundary_col,
        ].tolist()

        raise ValueError(
            "Duplicate district names in boundary file: "
            f"{duplicates}"
        )

    if ranking_data["_district_key"].duplicated().any():
        duplicates = ranking_data.loc[
            ranking_data["_district_key"].duplicated(keep=False),
            ranking_col,
        ].tolist()

        raise ValueError(
            "Duplicate district names in ranking file: "
            f"{duplicates}"
        )

    # Validate the three permitted categories.
    invalid_groups = (
        set(ranking_data["CCI_Group"].dropna().astype(str).unique())
        - set(CCI_GROUPS)
    )

    if invalid_groups:
        raise ValueError(
            "Unexpected CCI categories found: "
            f"{invalid_groups}. Expected only Q1, Q2 and Q3."
        )

    # Prepare only the fields required from the ranking file.
    ranking_clean = ranking_data[
        [
            "_district_key",
            "Rank",
            "PCA_CCI",
            "CCI_Group",
        ]
    ].copy()

    ranking_clean["Rank"] = pd.to_numeric(
        ranking_clean["Rank"],
        errors="coerce",
    )

    ranking_clean["PCA_CCI"] = pd.to_numeric(
        ranking_clean["PCA_CCI"],
        errors="coerce",
    )

    # Remove any existing fields from GeoJSON that could conflict
    # with the ranking fields. This prevents Rank_x / Rank_y.
    conflicting_columns = [
        "Rank",
        "Rank_x",
        "Rank_y",
        "PCA_CCI",
        "PCA_CCI_x",
        "PCA_CCI_y",
        "CCI_Group",
        "CCI_Group_x",
        "CCI_Group_y",
    ]

    boundaries = boundaries.drop(
        columns=[
            col for col in conflicting_columns
            if col in boundaries.columns
        ],
        errors="ignore",
    )

    # One-to-one merge: one polygon for each district and one
    # ranking record for each district.
    map_data = boundaries.merge(
        ranking_clean,
        on="_district_key",
        how="left",
        validate="one_to_one",
    )

    # Confirm that the expected columns exist after merging.
    for col in required_ranking_columns:
        if col not in map_data.columns:
            raise ValueError(
                f"Column '{col}' was not created by the merge. "
                f"Available columns: {list(map_data.columns)}"
            )

    # Identify boundary districts without matching ranking data.
    unmatched_map = map_data.loc[
        map_data["CCI_Group"].isna(),
        boundary_col,
    ].dropna().astype(str).tolist()

    # Identify ranking districts without matching polygons.
    unmatched_ranking = ranking_clean.loc[
        ~ranking_clean["_district_key"].isin(
            boundaries["_district_key"]
        ),
        "_district_key",
    ].tolist()

    if unmatched_map:
        st.warning(
            "No matching CCI ranking was found for these map "
            "districts: " + ", ".join(unmatched_map)
        )

    if unmatched_ranking:
        st.warning(
            "These ranking districts were not found in the "
            "boundary file: " + ", ".join(unmatched_ranking)
        )

    return map_data, boundary_col


# ============================================================
# 8. DRAW MAP WITH ONLY Q1, Q2 AND Q3
# ============================================================

def draw_cci_district_map(map_data, district_col):
    """
    Draw the district map using only:
    Q1 - Highest CCI
    Q2 - Medium CCI
    Q3 - Lowest CCI

    Missing matches are not assigned a fourth category and
    are not included in the legend.
    """

    if map_data is None or map_data.empty:
        raise ValueError(
            "There is no district map data to display."
        )

    if "CCI_Group" not in map_data.columns:
        raise ValueError(
            "CCI_Group is missing from the merged map data."
        )

    if "Rank" not in map_data.columns:
        raise ValueError(
            "Rank is missing from the merged map data."
        )

    fig, ax = plt.subplots(
        figsize=(13, 13),
    )

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Plot only the three requested CCI categories.
    for group in CCI_GROUPS:

        subset = map_data.loc[
            map_data["CCI_Group"] == group
        ]

        if not subset.empty:
            subset.plot(
                ax=ax,
                color=CCI_COLORS[group],
                edgecolor="black",
                linewidth=0.65,
                zorder=2,
            )

    # Label districts with district name and rank.
    for _, row in map_data.iterrows():

        geometry = row.geometry

        if geometry is None or geometry.is_empty:
            continue

        # Skip labels for unmatched districts.
        if row["CCI_Group"] not in CCI_GROUPS:
            continue

        point = geometry.representative_point()

        district_name = str(row[district_col])

        rank = row["Rank"]

        if pd.notna(rank):
            label = (
                f"{district_name}\n"
                f"Rank {int(rank)}"
            )
        else:
            label = district_name

        ax.annotate(
            label,
            xy=(point.x, point.y),
            ha="center",
            va="center",
            fontsize=6.5,
            fontweight="bold",
            color="black",
            zorder=5,
            bbox={
                "boxstyle": "round,pad=0.12",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.70,
            },
        )

    # Legend contains exactly three categories.
    legend_items = [
        mpatches.Patch(
            facecolor=CCI_COLORS[group],
            edgecolor="black",
            label=group,
        )
        for group in CCI_GROUPS
    ]

    ax.legend(
        handles=legend_items,
        title="CCI Rank Groups",
        loc="lower left",
        fontsize=9,
        title_fontsize=10,
        framealpha=0.95,
    )

    ax.set_title(
        "Maharashtra Climate Change Index (CCI)\n"
        "PCA-Based District Ranking: Q1, Q2 and Q3",
        fontsize=16,
        fontweight="bold",
        pad=18,
    )

    ax.set_axis_off()
    ax.set_aspect("equal")
    fig.tight_layout()

    return fig


# ============================================================
# 9. PAGE HEADER
# ============================================================

st.title("🌦️ District-wise Climate Change Index of Maharashtra")

st.subheader(
    "PCA-Based Analysis of 36 Districts"
)
st.divider()

# ============================================================
# 11. RANKING TABLE, SUMMARY AND BAR CHARTS
# ============================================================
# Load ranking data automatically from GitHub
ranking = None

try:
    if RANKING_FILE.exists():
        raw_ranking = pd.read_csv(RANKING_FILE)
        ranking = prepare_ranking(raw_ranking)
    else:
        st.error("CCI_Ranking.csv file not found in repository.")

except Exception as exc:
    st.error(f"Unable to load ranking data: {exc}")
if ranking is not None:

    st.success(
        "CCI ranking loaded successfully: "
        f"{len(ranking)} district records."
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Districts",
            ranking["District"].nunique(),
        )

    with col2:
        if ranking["PCA_CCI"].notna().any():
            st.metric(
                "Highest CCI",
                f"{ranking['PCA_CCI'].max():.4f}",
            )
        else:
            st.metric("Highest CCI", "N/A")

    with col3:
        if ranking["PCA_CCI"].notna().any():
            st.metric(
                "Lowest CCI",
                f"{ranking['PCA_CCI'].min():.4f}",
            )
        else:
            st.metric("Lowest CCI", "N/A")

    with col4:
        st.metric(
            "Rank Groups",
            ranking["CCI_Group"].nunique(),
        )

    st.divider()

    st.header("📊 District-Wise CCI Ranking")

    display_cols = [
        "Rank",
        "District",
        "PCA_CCI",
        "CCI_Group",
    ]

    st.dataframe(
        ranking[display_cols].sort_values("Rank"),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "⬇️ Download CCI Ranking CSV",
        data=ranking[display_cols].to_csv(
            index=False
        ).encode("utf-8"),
        file_name="Maharashtra_CCI_Ranking.csv",
        mime="text/csv",
    )

# ============================================================
# 12. MAHARASHTRA DISTRICT CCI MAP
# ============================================================

st.divider()

st.header("🗺️ Maharashtra District CCI Map")

st.markdown(
    """
    The map displays the three CCI categories:

    - **Q1 – Highest CCI**
    - **Q2 – Medium CCI**
    - **Q3 – Lowest CCI**
)
if ranking is None:

    st.warning("Load the CCI ranking data before displaying the map.")

else:

    try:
        boundaries = None

        # Load GeoJSON automatically from GitHub repository
        for map_path in MAP_CANDIDATES:

            if map_path.exists():

                boundaries = read_geojson_path(
                    str(map_path),
                    map_path.stat().st_mtime,
                )
                break

        # Online GeoJSON fallback
        if boundaries is None:

            try:
                boundaries = gpd.read_file(MAP_URL)

            except Exception:
                boundaries = None

        if boundaries is None:

            st.error(
                "Maharashtra district GeoJSON file not found."
            )

        else:

            map_data, district_col = merge_cci_map(
                boundaries,
                ranking,
            )

            matched_count = int(
                map_data["CCI_Group"]
                .isin(CCI_GROUPS)
                .sum()
            )

            st.write(
                f"Matched districts: {matched_count} "
                f"out of {len(ranking)} ranking records."
            )

            if matched_count == 0:

                st.error("No districts matched.")

            else:

                fig_map = draw_cci_district_map(
                    map_data,
                    district_col,
                )

                st.pyplot(
                    fig_map,
                    use_container_width=True,
                )

                plt.close(fig_map)

    except Exception as exc:

        st.error(f"Unable to generate CCI district map: {exc}")

if ranking is None:

    st.warning(
        "Load the CCI ranking data before displaying the map."
    )

else:

    try:

        boundaries = None

 
        if boundaries is None:

            st.info(
                "Upload a district boundary GeoJSON file, "
                "or add a supported GeoJSON file to your "
                "project folder."
            )

        else:

            map_data, district_col = merge_cci_map(
                boundaries,
                ranking,
            )

            matched_count = int(
                map_data["CCI_Group"]
                .isin(CCI_GROUPS)
                .sum()
            )

            st.write(
                f"Matched districts: {matched_count} "
                f"out of {len(ranking)} ranking records."
            )

            if matched_count == 0:

                st.error(
                    "No districts matched. Check district names "
                    "in your CSV and GeoJSON boundary file."
                )

            else:

                fig_map = draw_cci_district_map(
                    map_data,
                    district_col,
                )

                st.pyplot(
                    fig_map,
                    use_container_width=True,
                )

                plt.close(fig_map)

                st.subheader("CCI Group Summary")

                group_summary = (
                    map_data.loc[
                        map_data["CCI_Group"].isin(CCI_GROUPS),
                        "CCI_Group",
                    ]
                    .value_counts()
                    .reindex(CCI_GROUPS, fill_value=0)
                    .rename_axis("CCI Group")
                    .reset_index(name="District Count")
                )

                st.dataframe(
                    group_summary,
                    use_container_width=True,
                    hide_index=True,
                )

                with st.expander(
                    "View merged district map data"
                ):

                    map_display = map_data[
                        [
                            district_col,
                            "Rank",
                            "PCA_CCI",
                            "CCI_Group",
                        ]
                    ].rename(
                        columns={
                            district_col: "District"
                        }
                    )

                    st.dataframe(
                        map_display,
                        use_container_width=True,
                        hide_index=True,
                    )

    except Exception as exc:

        st.error(
            f"Unable to generate CCI district map: {exc}"
        )

        st.info(
            "Check that the ranking CSV contains district names, "
            "and that the GeoJSON contains Maharashtra district "
            "polygons with matching names."
        )

# ============================================================
# 22. FOOTER
# ============================================================

st.caption(
    "Maharashtra Climate Change Index | "
    "PCA-based district comparison | Python + Streamlit"
)
