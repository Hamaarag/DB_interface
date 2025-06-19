#!/usr/bin/env python3
"""
Coordinate Cleaning Script for Hamaarag Monitoring Data

This script identifies and resolves coordinate discrepancies for monitoring points
that appear multiple times in the dataset with different GPS coordinates.

For points with coordinates within 100m of each other, it uses the most recent coordinates.
For points with larger discrepancies, it flags them for manual curation and EXCLUDES
them from the cleaned output file. Flagged point groups must be manually resolved
before the data can be loaded into the database.
"""

import pandas as pd
import numpy as np
import argparse
import logging
from datetime import datetime
from geopy.distance import geodesic
from sklearn.neighbors import BallTree
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two GPS coordinates using geodesic distance.

    Returns:
        float: Distance in meters
    """
    try:
        return geodesic((lat1, lon1), (lat2, lon2)).meters
    except Exception:
        return float("inf")


def clean_coordinates(input_file, output_file, flagged_file, distance_threshold=100):
    """
    Clean coordinate discrepancies in monitoring data.

    Args:
        input_file: Path to input CSV file
        output_file: Path to output cleaned CSV file
        flagged_file: Path to output flagged discrepancies CSV file
        distance_threshold: Maximum distance (meters) for auto-correction
    """
    try:  # Read the source data
        logger.info(f"Reading data from {input_file}")
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} rows")

        # Use existing lat/lon fields directly
        logger.info("Using existing lat/lon coordinate fields...")
        df["latitude"] = pd.to_numeric(df["lat"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["lon"], errors="coerce")

        # Filter out rows with missing coordinates
        df_with_coords = df.dropna(subset=["latitude", "longitude"]).copy()
        df_without_coords = df[df["latitude"].isna() | df["longitude"].isna()].copy()

        logger.info(f"Found {len(df_with_coords)} rows with valid coordinates")
        logger.info(
            f"Found {len(df_without_coords)} rows without valid coordinates"
        )  # Group by unit, subunit, site, and point_name to find duplicates
        # dropna=False ensures rows with missing values in groupby columns are not excluded
        point_groups = df_with_coords.groupby(
            ["unit", "subunit", "site", "point_name"], dropna=False
        )

        # Calculate total unique point groups upfront
        unique_point_groups_count = len(point_groups)

        cleaned_rows = []
        flagged_rows = []
        cleaning_stats = {
            "total_points": 0,
            "unique_point_groups": unique_point_groups_count,
            "unique_points": 0,
            "auto_corrected": 0,
            "flagged_for_review": 0,
        }

        logger.info("Processing coordinate groups...")

        for group_key, group_df in point_groups:
            cleaning_stats["total_points"] += len(group_df)

            # Get unique coordinate pairs
            unique_coords = group_df[["latitude", "longitude"]].drop_duplicates()

            if len(unique_coords) == 1:
                # No coordinate discrepancy - keep all rows as is
                cleaned_rows.extend(group_df.to_dict("records"))
                cleaning_stats["unique_points"] += len(group_df)
            else:
                # Multiple coordinate sets for the same point
                unit, subunit, site, point_name = group_key
                logger.info(
                    f"Processing discrepancies for {unit}/{subunit}/{site}/{point_name}: {len(unique_coords)} coordinate sets"
                )

                # Calculate distances between all coordinate pairs
                coords_list = unique_coords.values.tolist()
                max_distance = 0

                for i in range(len(coords_list)):
                    for j in range(i + 1, len(coords_list)):
                        lat1, lon1 = coords_list[i]
                        lat2, lon2 = coords_list[j]
                        distance = calculate_distance(lat1, lon1, lat2, lon2)
                        max_distance = max(max_distance, distance)

                if max_distance <= distance_threshold:
                    # Auto-correct: use most recent coordinates
                    most_recent_coords = group_df.loc[group_df["year"].idxmax()]

                    # Update all rows in this group with the most recent coordinates
                    corrected_group = group_df.copy()
                    corrected_group["latitude"] = most_recent_coords["latitude"]
                    corrected_group["longitude"] = most_recent_coords["longitude"]
                    corrected_group["lat"] = most_recent_coords["latitude"]
                    corrected_group["lon"] = most_recent_coords["longitude"]

                    cleaned_rows.extend(corrected_group.to_dict("records"))
                    cleaning_stats["auto_corrected"] += len(group_df)

                    logger.info(
                        f"  Auto-corrected {len(group_df)} rows (max distance: {max_distance:.1f}m)"
                    )
                else:  # Flag for manual review
                    flagged_info = {
                        "unit": unit,
                        "subunit": subunit,
                        "site": site,
                        "point_name": point_name,
                        "max_distance_meters": max_distance,
                        "coordinate_count": len(unique_coords),
                        "row_count": len(group_df),
                    }

                    # Add all coordinate details first
                    for idx, (_, coord_row) in enumerate(unique_coords.iterrows()):
                        flagged_info[f"coordinates_{idx+1}"] = (
                            f"{coord_row['latitude']},{coord_row['longitude']}"
                        )
                    # Then add all year details (2-digit format)
                    for idx, (_, coord_row) in enumerate(unique_coords.iterrows()):
                        # Find years using these coordinates
                        years = group_df[
                            (group_df["latitude"] == coord_row["latitude"])
                            & (group_df["longitude"] == coord_row["longitude"])
                        ]["year"].unique()
                        # Convert to 2-digit format and sort
                        years_2digit = [
                            f"{int(year) % 100:02d}" for year in years if pd.notna(year)
                        ]
                        flagged_info[f"years_{idx+1}"] = ";".join(sorted(years_2digit))

                    flagged_rows.append(flagged_info)
                    cleaning_stats["flagged_for_review"] += len(group_df)

                    logger.warning(
                        f"  Flagged for review (max distance: {max_distance:.1f}m)"
                    )

        # Combine cleaned rows with rows that had no coordinates
        final_df = pd.DataFrame(cleaned_rows)
        if len(df_without_coords) > 0:
            final_df = pd.concat([final_df, df_without_coords], ignore_index=True)

        # Rename original coordinate fields to preserve them
        final_df = final_df.rename(columns={"lon": "orig_lon", "lat": "orig_lat"})

        logger.info(f"Writing cleaned data to {output_file}")  # Write outputs
        final_df.to_csv(output_file, index=False)

        if flagged_rows:
            logger.info("Finding nearest neighbors for flagged coordinates...")
            enhanced_flagged_rows = find_nearest_neighbors(flagged_rows, df_with_coords)

            logger.info(f"Writing flagged discrepancies to {flagged_file}")
            # Create DataFrame with explicit column ordering
            desired_columns = [
                "unit",
                "subunit",
                "site",
                "point_name",
                "max_distance_meters",
                "coordinate_count",
                "row_count",
                "coordinates_1",
                "coordinates_2",
                "coordinates_3",
                "years_1",
                "years_2",
                "years_3",
                "nearest_point_1_unit",
                "nearest_point_1_subunit",
                "nearest_point_1_site",
                "nearest_point_1_name",
                "nearest_point_1_distance_m",
                "nearest_point_1_years",
                "nearest_point_2_unit",
                "nearest_point_2_subunit",
                "nearest_point_2_site",
                "nearest_point_2_name",
                "nearest_point_2_distance_m",
                "nearest_point_2_years",
                "nearest_point_3_unit",
                "nearest_point_3_subunit",
                "nearest_point_3_site",
                "nearest_point_3_name",
                "nearest_point_3_distance_m",
                "nearest_point_3_years",
            ]

            # Create DataFrame and ensure column order
            flagged_df = pd.DataFrame(enhanced_flagged_rows)

            # Reorder columns according to desired order, only including columns that exist
            existing_columns = [
                col for col in desired_columns if col in flagged_df.columns
            ]
            flagged_df = flagged_df[existing_columns]

            flagged_df.to_csv(flagged_file, index=False)

        # Print summary statistics
        logger.info("=== COORDINATE CLEANING SUMMARY ===")
        logger.info(f"Total rows processed: {len(df)}")
        logger.info(f"Rows with valid coordinates: {len(df_with_coords)}")
        logger.info(f"Rows without coordinates: {len(df_without_coords)}")
        logger.info(
            f"Unique point groups examined: {cleaning_stats['unique_point_groups']}"
        )
        logger.info(
            f"Rows that contain points with unique coordinates: {cleaning_stats['unique_points']}"
        )
        logger.info(
            f"Rows that contain points that were auto-corrected (≤{distance_threshold}m): {cleaning_stats['auto_corrected']}"
        )
        logger.info(
            f"Rows that contain points that were flagged for review (>{distance_threshold}m): {cleaning_stats['flagged_for_review']}"
        )

        if flagged_rows:
            logger.warning(f"\n⚠️  MANUAL CURATION REQUIRED ⚠️")
            logger.warning(
                f"Found {len(flagged_rows)} point groups with coordinate discrepancies > {distance_threshold}m"
            )
            logger.warning(f"Review flagged discrepancies in: {flagged_file}")
            logger.warning(
                f"Fix source data or create coordinate overrides before loading."
            )
            return False
        else:
            logger.info(f"\n✅ All coordinate discrepancies resolved automatically")
            logger.info(f"Cleaned data ready for loading: {output_file}")
            return True

    except Exception as e:
        logger.error(f"Error during coordinate cleaning: {e}")
        raise


def find_nearest_neighbors(flagged_rows, df_with_coords):
    """
    For each flagged coordinate, find the nearest point from the entire dataset using BallTree.

    Args:
        flagged_rows: List of flagged coordinate discrepancies
        df_with_coords: DataFrame containing all points with valid coordinates

    Returns:
        Enhanced flagged_rows with nearest neighbor information
    """
    if not flagged_rows:
        return flagged_rows
    # Create distinct combinations of sampling point and coordinates for BallTree
    # This avoids duplicates from multiple observations at the same point with same coordinates
    logger.info("Creating distinct point-coordinate combinations for spatial index...")
    distinct_points = (
        df_with_coords.groupby(
            ["unit", "subunit", "site", "point_name", "latitude", "longitude"],
            dropna=False,
        )
        .agg(
            {
                "year": lambda x: ";".join(
                    [
                        f"{int(year) % 100:02d}"
                        for year in sorted(x.unique())
                        if pd.notna(year)
                    ]
                )
            }
        )
        .reset_index()
    )

    logger.info(
        f"Reduced from {len(df_with_coords)} observations to {len(distinct_points)} distinct point-coordinate combinations"
    )

    # Prepare data for BallTree using distinct points only
    # Convert lat/lon to radians for haversine distance calculation
    coords = distinct_points[["latitude", "longitude"]].values
    coords_rad = np.radians(coords)

    # Build BallTree index (one-time cost)
    logger.info("Building spatial index for nearest neighbor search...")
    tree = BallTree(coords_rad, metric="haversine")

    enhanced_flagged_rows = []

    for flagged_point in flagged_rows:
        enhanced_point = flagged_point.copy()
        # Extract all flagged coordinates for this point
        flagged_coords = []
        coord_idx = 1
        while f"coordinates_{coord_idx}" in flagged_point:
            coord_str = flagged_point[f"coordinates_{coord_idx}"]
            lat, lon = map(float, coord_str.split(","))
            flagged_coords.append((lat, lon, coord_idx))
            coord_idx += 1

        # Collect all nearest neighbor information first
        nearest_neighbor_info = (
            {}
        )  # For each flagged coordinate, find nearest neighbor using BallTree
        for lat, lon, idx in flagged_coords:
            # Convert query point to radians
            query_point = np.radians([[lat, lon]])
            # Find all nearest neighbors (we'll only filter out the exact same point-coordinate combination)
            k_neighbors = min(10, len(distinct_points))  # Get up to 10 neighbors
            distances, indices = tree.query(query_point, k=k_neighbors)

            # Convert distances back to meters (haversine returns distances in radians)
            # Earth radius ≈ 6371 km
            distances_m = distances[0] * 6371000  # Convert to meters

            # Find the first neighbor that's not the exact same point-coordinate combination
            nearest_point = None
            min_distance = float("inf")

            for i, dist_m in enumerate(distances_m):
                candidate_idx = indices[0][i]
                candidate_row = distinct_points.iloc[candidate_idx]

                # Skip ONLY if this is the exact same point-coordinate combination
                # (same point name AND same coordinates)
                # Handle NaN values correctly in comparisons
                def safe_equal(a, b):
                    if pd.isna(a) and pd.isna(b):
                        return True
                    elif pd.isna(a) or pd.isna(b):
                        return False
                    else:
                        return a == b
                
                if (
                    safe_equal(candidate_row["unit"], flagged_point["unit"])
                    and safe_equal(candidate_row["subunit"], flagged_point["subunit"])
                    and safe_equal(candidate_row["site"], flagged_point["site"])
                    and safe_equal(candidate_row["point_name"], flagged_point["point_name"])
                    and abs(candidate_row["latitude"] - lat) < 1e-5
                    and abs(candidate_row["longitude"] - lon) < 1e-5
                ):
                    continue

                # Accept all other combinations:
                # - Other coordinates from the same point group
                # - Same coordinates but different point names
                # - Different point groups with different coordinates
                nearest_point = candidate_row
                min_distance = dist_m
                break

            if nearest_point is not None:
                # Store nearest neighbor info for this coordinate (don't add to enhanced_point yet)
                nearest_neighbor_info[f"nearest_point_{idx}_unit"] = nearest_point[
                    "unit"
                ]
                nearest_neighbor_info[f"nearest_point_{idx}_subunit"] = nearest_point[
                    "subunit"
                ]
                nearest_neighbor_info[f"nearest_point_{idx}_site"] = nearest_point[
                    "site"
                ]
                nearest_neighbor_info[f"nearest_point_{idx}_name"] = nearest_point[
                    "point_name"
                ]
                nearest_neighbor_info[f"nearest_point_{idx}_distance_m"] = round(
                    min_distance, 1
                )
                # Use the aggregated years from distinct_points
                nearest_neighbor_info[f"nearest_point_{idx}_years"] = nearest_point[
                    "year"
                ]  # Create properly ordered enhanced point following the desired column order:
        # 1-9, 24, 10, 11, 25, 12-23, 26-31
        ordered_point = {}

        # Columns 1-9: basic info + coordinates_1, coordinates_2
        basic_cols = [
            "unit",
            "subunit",
            "site",
            "point_name",
            "max_distance_meters",
            "coordinate_count",
            "row_count",
            "coordinates_1",
            "coordinates_2",
        ]
        for col in basic_cols:
            if col in flagged_point:
                ordered_point[col] = flagged_point[col]

        # Position 10 (originally column 24): coordinates_3 (if exists)
        if "coordinates_3" in flagged_point:
            ordered_point["coordinates_3"] = flagged_point["coordinates_3"]
        # Positions 11-12 (originally columns 10-11): years_1, years_2
        if "years_1" in flagged_point:
            ordered_point["years_1"] = flagged_point["years_1"]
        if "years_2" in flagged_point:
            ordered_point["years_2"] = flagged_point["years_2"]

        # Position 13 (originally column 25): years_3 (if exists)
        if "years_3" in flagged_point:
            ordered_point["years_3"] = flagged_point["years_3"]

        # Positions 14-25 (originally columns 12-23): nearest_point_1_* and nearest_point_2_* fields
        nearest_1_cols = [
            "nearest_point_1_unit",
            "nearest_point_1_subunit",
            "nearest_point_1_site",
            "nearest_point_1_name",
            "nearest_point_1_distance_m",
            "nearest_point_1_years",
        ]
        nearest_2_cols = [
            "nearest_point_2_unit",
            "nearest_point_2_subunit",
            "nearest_point_2_site",
            "nearest_point_2_name",
            "nearest_point_2_distance_m",
            "nearest_point_2_years",
        ]

        for col in nearest_1_cols + nearest_2_cols:
            if col in nearest_neighbor_info:
                ordered_point[col] = nearest_neighbor_info[col]
        # Positions 26-31 (originally columns 26-31): nearest_point_3_* fields (if exists)
        nearest_3_cols = [
            "nearest_point_3_unit",
            "nearest_point_3_subunit",
            "nearest_point_3_site",
            "nearest_point_3_name",
            "nearest_point_3_distance_m",
            "nearest_point_3_years",
        ]
        for col in nearest_3_cols:
            if col in nearest_neighbor_info:
                ordered_point[col] = nearest_neighbor_info[col]

        enhanced_flagged_rows.append(ordered_point)

    return enhanced_flagged_rows


def main():
    parser = argparse.ArgumentParser(
        description="Clean coordinate discrepancies in monitoring data"
    )
    parser.add_argument("--input", required=True, help="Input CSV file path")
    parser.add_argument(
        "--output",
        help="Output cleaned CSV file path (default: adds '_cleaned_mult_coord' suffix)",
    )
    parser.add_argument(
        "--flagged",
        help="Output flagged discrepancies CSV file path (default: adds '_flagged' suffix)",
    )
    parser.add_argument(
        "--distance-threshold",
        type=float,
        default=100.0,
        help="Maximum distance in meters for auto-correction (default: 100)",
    )

    args = parser.parse_args()

    # Generate default output filenames if not provided
    input_base = os.path.splitext(args.input)[0]
    output_file = args.output or f"{input_base}_cleaned_mult_coord.csv"
    flagged_file = args.flagged or f"{input_base}_flagged_coordinates.csv"

    try:
        success = clean_coordinates(
            args.input, output_file, flagged_file, args.distance_threshold
        )

        if not success:
            sys.exit(1)  # Exit with error code if manual curation is required

    except Exception as e:
        logger.error(f"Failed to clean coordinates: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
