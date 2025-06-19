#!/usr/bin/env python3
"""
Coordinate Conflict Detection and Resolution Script for Hamaarag Monitoring Data

This script identifies cases where different sampling point names share the same coordinates,
which would violate the unique_coordinates constraint in the database schema.

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


def detect_coordinate_conflicts(input_file, output_file, coordinate_precision=1e-5):
    """
    Detect and resolve coordinate conflicts where different point names share the same coordinates.
    
    For conflicts within the same unit and site, automatically applies the suggested fix.
    For conflicts across different units or sites, flags them for manual review.

    Args:
        input_file: Path to cleaned CSV file from clean_coordinates.py
        output_file: Path to output conflicts CSV file
        coordinate_precision: Tolerance for coordinate matching (default: 1e-5 degrees)
        
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
                ["unit", "subunit", "site", "point_name", "latitude", "longitude"],
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
        )        # Group by coordinates (with precision tolerance) to find conflicts
        logger.info("Detecting coordinate conflicts...")
        conflicts = []
        corrections_made = []
        
        # Create a copy of the input data for applying automatic fixes
        df_corrected = df.copy()

        # Round coordinates to specified precision for grouping
        precision_factor = 1 / coordinate_precision
        distinct_points["lat_rounded"] = (
            np.round(distinct_points["latitude"] * precision_factor) / precision_factor
        )
        distinct_points["lon_rounded"] = (
            np.round(distinct_points["longitude"] * precision_factor) / precision_factor
        )

        coord_groups = distinct_points.groupby(["lat_rounded", "lon_rounded"])

        conflict_count = 0
        auto_fixed_count = 0
        for (lat_rounded, lon_rounded), group in coord_groups:
            # Check if multiple point names share these coordinates
            unique_points = group[
                ["unit", "subunit", "site", "point_name"]
            ].drop_duplicates()

            if len(unique_points) > 1:
                conflict_count += 1

                # Get all the details for this coordinate conflict
                units = sorted(group["unit"].unique())
                subunits = sorted(
                    [str(x) for x in group["subunit"].unique() if pd.notna(x)]
                )
                sites = sorted(group["site"].unique())
                point_names = sorted(group["point_name"].unique())
                years = sorted(
                    set(
                        [
                            year
                            for year_list in group["year"]
                            for year in year_list.split(";")
                            if year
                        ]
                    )
                )                # Determine if this can be auto-fixed or needs manual review
                if len(set(units)) == 1 and len(set(sites)) == 1:
                    # Same unit and site - apply automatic fix
                    latest_year = max([int(year) for year in years])
                    latest_points = group[group["year"].str.contains(str(latest_year))]
                    
                    if len(latest_points) > 0:
                        target_point_name = latest_points.iloc[0]['point_name']
                        auto_fixed_count += 1
                        
                        # Apply the fix to the corrected dataframe
                        for _, point_row in unique_points.iterrows():
                            if point_row['point_name'] != target_point_name:
                                # Update all rows matching this point to use the target point name
                                mask = (
                                    (df_corrected['unit'] == point_row['unit']) &
                                    (df_corrected['subunit'] == point_row['subunit'] if pd.notna(point_row['subunit']) 
                                     else df_corrected['subunit'].isna()) &
                                    (df_corrected['site'] == point_row['site']) &
                                    (df_corrected['point_name'] == point_row['point_name']) &
                                    (abs(df_corrected['latitude'] - lat_rounded) < coordinate_precision) &
                                    (abs(df_corrected['longitude'] - lon_rounded) < coordinate_precision)
                                )
                                
                                rows_updated = mask.sum()
                                df_corrected.loc[mask, 'point_name'] = target_point_name
                                
                                # Log the correction
                                correction_info = {
                                    'coordinates': f"{lat_rounded},{lon_rounded}",
                                    'old_point_name': point_row['point_name'],
                                    'new_point_name': target_point_name,
                                    'unit': point_row['unit'],
                                    'subunit': point_row['subunit'] if pd.notna(point_row['subunit']) else 'N/A',
                                    'site': point_row['site'],
                                    'reason': f"Most recent year: {latest_year}",
                                    'rows_affected': rows_updated
                                }
                                corrections_made.append(correction_info)
                        
                        logger.info(f"Auto-fixed conflict at {lat_rounded},{lon_rounded}: kept '{target_point_name}' (most recent: {latest_year})")
                        continue  # Skip adding to conflicts list
                
                # If we reach here, it needs manual review
                suggested_fix = "Manual review required - different units/sites" if len(set(units)) > 1 or len(set(sites)) > 1 else "Manual review required"

                conflict_info = {
                    "coordinates": f"{lat_rounded},{lon_rounded}",
                    "conflict_count": len(unique_points),
                    "units": ";".join(units),
                    "subunits": ";".join(subunits) if subunits else "",
                    "sites": ";".join(sites),
                    "point_names": ";".join(point_names),
                    "years": ";".join(years),
                    "suggested_fix": suggested_fix,
                }

                conflicts.append(conflict_info)

                logger.warning(
                    f"Conflict at {lat_rounded},{lon_rounded}: {len(unique_points)} different points"
                )
                for _, point in unique_points.iterrows():
                    logger.warning(
                        f"  - {point['unit']}/{point['subunit']}/{point['site']}/{point['point_name']}"
                    )        # Generate output file names
        input_base = os.path.splitext(input_file)[0]
        cleaned_output_file = f"{input_base}_point_names_cleaned.csv"
        corrections_log_file = f"{input_base}_point_name_corrections.md"
        
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
                    f.write("| Coordinates | Unit | Site | Old Point Name | New Point Name | Reason | Rows Affected |\n")
                    f.write("|-------------|------|------|----------------|----------------|--------|---------------|\n")
                    
                    for correction in corrections_made:
                        f.write(f"| {correction['coordinates']} | {correction['unit']} | {correction['site']} | ")
                        f.write(f"{correction['old_point_name']} | {correction['new_point_name']} | ")
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
                    "subunits",
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
        "--output",
        help="Output conflicts CSV file path (default: adds '_coordinate_conflicts' suffix)",
    )
    parser.add_argument(
        "--coordinate-precision",
        type=float,
        default=1e-5,
        help="Coordinate precision tolerance in degrees (default: 1e-5)",
    )

    args = parser.parse_args()    # Generate default output filename if not provided
    input_base = os.path.splitext(args.input)[0]
    output_file = args.output or f"{input_base}_coordinate_conflicts.csv"

    try:
        success, cleaned_file, corrections_file = detect_coordinate_conflicts(
            args.input, output_file, args.coordinate_precision
        )
        
        logger.info(f"\n📁 OUTPUT FILES:")
        logger.info(f"   Cleaned data: {cleaned_file}")
        logger.info(f"   Corrections log: {corrections_file}")
        logger.info(f"   Conflicts (if any): {output_file}")

        if not success:
            sys.exit(1)  # Exit with error code if manual conflicts remain

    except Exception as e:
        logger.error(f"Failed to process coordinate conflicts: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
