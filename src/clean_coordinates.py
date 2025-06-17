#!/usr/bin/env python3
"""
Coordinate Cleaning Script for Hamaarag Monitoring Data

This script identifies and resolves coordinate discrepancies for monitoring points
that appear multiple times in the dataset with different GPS coordinates.

For points with coordinates within 100m of each other, it uses the most recent coordinates.
For points with larger discrepancies, it flags them for manual curation.
"""

import pandas as pd
import numpy as np
import argparse
import logging
from datetime import datetime
from geopy.distance import geodesic
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
        logger.info(f"Found {len(df_without_coords)} rows without valid coordinates")

        # Group by unit, subunit, site, and point_name to find duplicates
        point_groups = df_with_coords.groupby(["unit", "subunit", "site", "point_name"])
        
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
                else:
                    # Flag for manual review
                    flagged_info = {
                        "unit": unit,
                        "subunit": subunit,
                        "site": site,
                        "point_name": point_name,
                        "max_distance_meters": max_distance,
                        "coordinate_count": len(unique_coords),
                        "row_count": len(group_df),
                    }

                    # Add coordinate details
                    for idx, (_, coord_row) in enumerate(unique_coords.iterrows()):
                        flagged_info[f"coordinates_{idx+1}"] = (
                            f"{coord_row['latitude']},{coord_row['longitude']}"
                        )
                        # Find campaigns using these coordinates
                        campaigns = group_df[
                            (group_df["latitude"] == coord_row["latitude"])
                            & (group_df["longitude"] == coord_row["longitude"])
                        ]["campaign"].unique()
                        flagged_info[f"campaigns_{idx+1}"] = ";".join(campaigns)

                    flagged_rows.append(flagged_info)
                    cleaning_stats["flagged_for_review"] += len(group_df)

                    logger.warning(
                        f"  Flagged for review (max distance: {max_distance:.1f}m)"
                    )

        # Combine cleaned rows with rows that had no coordinates
        final_df = pd.DataFrame(cleaned_rows)
        if len(df_without_coords) > 0:
            final_df = pd.concat([final_df, df_without_coords], ignore_index=True)
        logger.info(f"Writing cleaned data to {output_file}")        # Write outputs
        final_df.to_csv(output_file, index=False)

        if flagged_rows:
            logger.info("Finding nearest neighbors for flagged coordinates...")
            enhanced_flagged_rows = find_nearest_neighbors(flagged_rows, df_with_coords)
            
            logger.info(f"Writing flagged discrepancies to {flagged_file}")
            flagged_df = pd.DataFrame(flagged_rows)
            flagged_df.to_csv(flagged_file, index=False)

        # Print summary statistics
        logger.info("=== COORDINATE CLEANING SUMMARY ===")
        logger.info(f"Total rows processed: {len(df)}")
        logger.info(f"Rows with valid coordinates: {len(df_with_coords)}")
        logger.info(f"Rows without coordinates: {len(df_without_coords)}")
        logger.info(f"Unique point groups examined: {cleaning_stats['unique_point_groups']}")
        logger.info(
            f"Points with unique coordinates: {cleaning_stats['unique_points']}"
        )
        logger.info(
            f"Points auto-corrected (≤{distance_threshold}m): {cleaning_stats['auto_corrected']}"
        )
        logger.info(
            f"Points flagged for review (>{distance_threshold}m): {cleaning_stats['flagged_for_review']}"
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
    For each flagged coordinate, find the nearest point from the entire dataset.
    
    Args:
        flagged_rows: List of flagged coordinate discrepancies
        df_with_coords: DataFrame containing all points with valid coordinates
    
    Returns:
        Enhanced flagged_rows with nearest neighbor information
    """
    enhanced_flagged_rows = []
    
    for flagged_point in flagged_rows:
        enhanced_point = flagged_point.copy()
        
        # Extract all flagged coordinates for this point
        flagged_coords = []
        coord_idx = 1
        while f"coordinates_{coord_idx}" in flagged_point:
            coord_str = flagged_point[f"coordinates_{coord_idx}"]
            lat, lon = map(float, coord_str.split(','))
            flagged_coords.append((lat, lon, coord_idx))
            coord_idx += 1
        
        # For each flagged coordinate, find nearest neighbor
        for lat, lon, idx in flagged_coords:
            min_distance = float('inf')
            nearest_point = None
            
            # Check against all points in the dataset
            for _, row in df_with_coords.iterrows():
                # Skip if this is the same point group
                if (row['unit'] == flagged_point['unit'] and 
                    row['subunit'] == flagged_point['subunit'] and
                    row['site'] == flagged_point['site'] and
                    row['point_name'] == flagged_point['point_name']):
                    continue
                
                distance = calculate_distance(lat, lon, row['latitude'], row['longitude'])
                if distance < min_distance:
                    min_distance = distance
                    nearest_point = row
            
            if nearest_point is not None:
                # Add nearest neighbor info for this coordinate
                enhanced_point[f"nearest_point_{idx}_unit"] = nearest_point['unit']
                enhanced_point[f"nearest_point_{idx}_subunit"] = nearest_point['subunit']
                enhanced_point[f"nearest_point_{idx}_site"] = nearest_point['site']
                enhanced_point[f"nearest_point_{idx}_name"] = nearest_point['point_name']
                enhanced_point[f"nearest_point_{idx}_distance_m"] = round(min_distance, 1)
                  # Find all campaigns for this nearest point
                nearest_campaigns = df_with_coords[
                    (df_with_coords['unit'] == nearest_point['unit']) &
                    (df_with_coords['subunit'] == nearest_point['subunit']) &
                    (df_with_coords['site'] == nearest_point['site']) &
                    (df_with_coords['point_name'] == nearest_point['point_name'])
                ]['campaign'].unique()
                enhanced_point[f"nearest_point_{idx}_campaigns"] = ';'.join(nearest_campaigns)
        
        enhanced_flagged_rows.append(enhanced_point)
    
    return enhanced_flagged_rows


def main():
    parser = argparse.ArgumentParser(
        description="Clean coordinate discrepancies in monitoring data"
    )
    parser.add_argument("--input", required=True, help="Input CSV file path")
    parser.add_argument(
        "--output",
        help="Output cleaned CSV file path (default: adds '_cleaned' suffix)",
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
    output_file = args.output or f"{input_base}_cleaned.csv"
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
