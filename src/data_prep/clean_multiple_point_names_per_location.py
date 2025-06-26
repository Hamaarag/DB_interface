#!/usr/bin/env python3
"""
Coordinate Conflict Detection and Resolution Script for Hamaarag Monitoring Data

This script identifies cases where different sampling point names share the same coordinates,
which would violate the unique_coordinates constraint in the database schema.

Coordinate comparison is precision-based, not exact matching. Two coordinates are considered
the same if they are within a configurable tolerance (default: 1e-4 degrees ≈ 11m).

For conflicts within the same unit and site, it automatically applies fixes by keeping
the most recent point name. For conflicts across different units or sites, it flags
them for manual review.

This script should be run on the cleaned data output by clean_coordinates.py as part of
the data preparation workflow before database loading.

Outputs:
- Cleaned CSV file with automatic fixes applied
- Markdown file documenting all corrections made
- Conflicts CSV file with remaining issues requiring manual review
"""

import pandas as pd
import numpy as np
import argparse
import logging
import sys
import os
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def detect_coordinate_conflicts(input_file, output_file, coordinate_precision=1e-4, cleaned_output_file=None):
    """
    Detect and resolve coordinate conflicts where different point names share the same coordinates.
    
    Coordinate comparison is precision-based, not exact matching. Two coordinates are considered
    the same if they are within the specified tolerance (coordinate_precision) of each other.
    
    For conflicts within the same unit and site, automatically applies the suggested fix.
    For conflicts across different units or sites, flags them for manual review.

    Args:
        input_file: Path to cleaned CSV file from clean_coordinates.py
        output_file: Path to output conflicts CSV file
        coordinate_precision: Tolerance for coordinate matching (default: 1e-4 degrees ≈ 11m)
        cleaned_output_file: Optional path for cleaned output file. If None, generates default name.
        
    Returns:
        Tuple of (success, cleaned_output_file, corrections_log_file)
    """
    try:
        logger.info(f"Reading cleaned data from {input_file}")
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} rows")

        # Filter out rows with missing coordinates
        df_with_coords = df.dropna(subset=["latitude", "longitude"]).copy()
        logger.info(f"Found {len(df_with_coords)} rows with valid coordinates")

        # Create distinct point-coordinate combinations
        logger.info("Creating distinct point-coordinate combinations...")
        distinct_points = (
            df_with_coords.groupby(
                ["unit", "site", "point_name", "latitude", "longitude"],
                dropna=False,
            )
            .agg(
                {
                    "year": lambda x: ";".join(
                        [
                            str(int(year))
                            for year in sorted(x.unique())
                            if pd.notna(year)
                        ]
                    )
                }
            )
            .reset_index()
        )

        logger.info(
            f"Found {len(distinct_points)} distinct point-coordinate combinations"
        )
        # Group by coordinates (with precision tolerance) to find conflicts
        logger.info("Detecting coordinate conflicts...")
        corrections_made = []
        
        # Create a copy of the input data for applying automatic fixes
        df_corrected = df.copy()

        # Truncate coordinates to specified precision for grouping
        # Calculate number of decimal places from coordinate precision
        decimal_places = int(-np.log10(coordinate_precision))
        precision_factor = 10 ** decimal_places
        distinct_points["lat_rounded"] = np.floor(distinct_points["latitude"] * precision_factor) / precision_factor
        distinct_points["lon_rounded"] = np.floor(distinct_points["longitude"] * precision_factor) / precision_factor

        # Group by unit, site, and rounded coordinates
        coord_groups = distinct_points.groupby(["unit", "site", "lat_rounded", "lon_rounded"])

        conflict_count = 0
        auto_fixed_count = 0
        conflicts = []

        for (unit, site, lat_rounded, lon_rounded), group in coord_groups:
            # Check if multiple point names exist for this location
            unique_point_names = group["point_name"].unique()
            
            if len(unique_point_names) > 1:
                conflict_count += 1
                
                # Find the most recent year across all points at this location
                all_years = []
                for year_list in group["year"]:
                    all_years.extend([int(year) for year in year_list.split(";") if year])
                
                latest_year = max(all_years)
                
                # Find a point name from the latest year
                latest_points = group[group["year"].str.contains(str(latest_year))]
                target_point_name = latest_points.iloc[0]['point_name']
                target_latitude = latest_points.iloc[0]['latitude']
                target_longitude = latest_points.iloc[0]['longitude']
                
                # Apply the fix to ALL rows with these coordinates (regardless of current point name)
                mask = (
                    (df_corrected['unit'] == unit) &
                    (df_corrected['site'] == site) &
                    (np.floor(df_corrected['latitude'] * precision_factor) / precision_factor == lat_rounded) &
                    (np.floor(df_corrected['longitude'] * precision_factor) / precision_factor == lon_rounded)
                )
                
                # Only count rows that actually need to change (not already the target name)
                rows_to_change_mask = mask & (df_corrected['point_name'] != target_point_name)
                rows_updated = rows_to_change_mask.sum()
                
                if rows_updated > 0:
                    # Get the point names that will be changed (excluding the target)
                    old_point_names = [name for name in unique_point_names if name != target_point_name]
                    
                    # Apply the changes - both point name AND coordinates
                    df_corrected.loc[mask, 'point_name'] = target_point_name
                    df_corrected.loc[mask, 'latitude'] = target_latitude
                    df_corrected.loc[mask, 'longitude'] = target_longitude
                    
                    # Log the correction
                    correction_info = {
                        'coordinates': f"{lat_rounded},{lon_rounded}",
                        'target_coordinates': f"{target_latitude},{target_longitude}",
                        'old_point_names': ";".join(old_point_names),
                        'new_point_name': target_point_name,
                        'unit': unit,
                        'site': site,
                        'reason': f"Most recent year: {latest_year}",
                        'rows_affected': rows_updated
                    }
                    corrections_made.append(correction_info)
                
                auto_fixed_count += 1
                logger.info(f"Auto-fixed conflict at {unit}/{site} ({lat_rounded},{lon_rounded}): standardized to '{target_point_name}' at ({target_latitude},{target_longitude}) (most recent: {latest_year})")
          # Generate output file names
        input_base = os.path.splitext(input_file)[0]
        if cleaned_output_file is None:
            # Default naming convention based on expected workflow
            if input_file.endswith("_cleaned_mult_coord.csv"):
                cleaned_output_file = input_file.replace("_cleaned_mult_coord.csv", "_cleaned.csv")
            else:
                cleaned_output_file = f"{input_base}_point_names_cleaned.csv"
        
        # Log file naming convention
        if cleaned_output_file.endswith("_cleaned.csv"):
            corrections_log_file = cleaned_output_file.replace("_cleaned.csv", "_cleaned.md")
        else:
            corrections_log_file = f"{os.path.splitext(cleaned_output_file)[0]}_corrections.md"
        
        # Write cleaned data
        logger.info(f"Writing cleaned data to {cleaned_output_file}")
        df_corrected.to_csv(cleaned_output_file, index=False)
        
        # Write corrections log
        if corrections_made:
            logger.info(f"Writing corrections log to {corrections_log_file}")
            with open(corrections_log_file, 'w') as f:
                f.write("# Point Name Corrections Applied\n\n")
                f.write(f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Input file:** {input_file}\n")
                f.write(f"**Cleaned output file:** {cleaned_output_file}\n\n")
                f.write(f"## Summary\n\n")
                f.write(f"- **Total conflicts detected:** {conflict_count + auto_fixed_count}\n")
                f.write(f"- **Automatically fixed:** {auto_fixed_count}\n")
                f.write(f"- **Requiring manual review:** {len(conflicts)}\n")
                f.write(f"- **Total rows affected:** {sum(c['rows_affected'] for c in corrections_made)}\n\n")
                
                if corrections_made:
                    f.write("## Automatic Corrections Applied\n\n")
                    f.write("| Grouped Coordinates | Target Coordinates | Unit | Site | Old Point Names | New Point Name | Reason | Rows Affected |\n")
                    f.write("|--------------------|--------------------|------|------|-----------------|----------------|--------|---------------|\n")
                    
                    for correction in corrections_made:
                        f.write(f"| {correction['coordinates']} | {correction['target_coordinates']} | {correction['unit']} | {correction['site']} | ")
                        f.write(f"{correction['old_point_names']} | {correction['new_point_name']} | ")
                        f.write(f"{correction['reason']} | {correction['rows_affected']} |\n")
                
                if conflicts:
                    f.write(f"\n## Conflicts Requiring Manual Review\n\n")
                    f.write(f"See detailed conflicts in: `{output_file}`\n\n")
                    f.write("These conflicts involve different units or sites and require manual resolution.\n")

        # Write remaining conflicts to CSV  
        if conflicts:
            logger.info(f"Writing {len(conflicts)} unresolved conflicts to {output_file}")
            conflicts_df = pd.DataFrame(conflicts)
            conflicts_df.to_csv(output_file, index=False)
        else:
            # Create empty conflicts file
            empty_df = pd.DataFrame(
                columns=[
                    "coordinates",
                    "conflict_count", 
                    "units",
                    "sites",
                    "point_names",
                    "years",
                    "suggested_fix",
                ]
            )
            empty_df.to_csv(output_file, index=False)

        # Summary logging
        if auto_fixed_count > 0:
            logger.info(f"\n✅ AUTOMATIC FIXES APPLIED")
            logger.info(f"Fixed {auto_fixed_count} coordinate conflicts automatically")
            logger.info(f"Total rows affected: {sum(c['rows_affected'] for c in corrections_made)}")
            logger.info(f"Corrections logged in: {corrections_log_file}")
            
        if conflicts:
            logger.warning(f"\n⚠️  MANUAL REVIEW REQUIRED")
            logger.warning(f"Found {len(conflicts)} conflicts requiring manual resolution")
            logger.warning(f"Review conflicts in: {output_file}")
            
        if not conflicts and auto_fixed_count == 0:
            logger.info(f"\n✅ No coordinate conflicts detected")
            
        logger.info(f"Cleaned data ready: {cleaned_output_file}")
        
        return (len(conflicts) == 0, cleaned_output_file, corrections_log_file)

    except Exception as e:
        logger.error(f"Error during conflict detection: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Detect coordinate conflicts where different point names share the same coordinates"
    )
    parser.add_argument("--input", required=True, help="Input cleaned CSV file path")
    parser.add_argument(
        "--cleaned-output",
        help="Output cleaned CSV file path (default: replaces '_cleaned_mult_coord.csv' with '_cleaned.csv')",
    )
    parser.add_argument(
        "--conflicts-output",
        help="Output conflicts CSV file path (default: adds '_coordinate_conflicts' suffix)",
    )
    parser.add_argument(
        "--coordinate-precision",
        type=float,
        default=1e-4,
        help="Coordinate precision tolerance in degrees (default: 1e-4)",
    )

    args = parser.parse_args()
      # Generate default output filenames if not provided
    input_base = os.path.splitext(args.input)[0]
    
    # Default naming convention based on expected workflow
    if args.input.endswith("_cleaned_mult_coord.csv"):
        # Standard workflow: input is from clean_coordinates.py output
        default_cleaned = args.input.replace("_cleaned_mult_coord.csv", "_cleaned.csv")
    else:
        # Fallback for other input files
        default_cleaned = f"{input_base}_point_names_cleaned.csv"
    
    cleaned_output_file = args.cleaned_output or default_cleaned
    conflicts_output_file = args.conflicts_output or f"{input_base}_coordinate_conflicts.csv"

    try:
        success, cleaned_file, corrections_file = detect_coordinate_conflicts(
            args.input, conflicts_output_file, args.coordinate_precision, cleaned_output_file
        )
        
        logger.info(f"\n📁 OUTPUT FILES:")
        logger.info(f"   Cleaned data: {cleaned_file}")
        logger.info(f"   Corrections log: {corrections_file}")
        logger.info(f"   Conflicts (if any): {conflicts_output_file}")

        if not success:
            sys.exit(1)  # Exit with error code if manual conflicts remain

    except Exception as e:
        logger.error(f"Failed to process coordinate conflicts: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
