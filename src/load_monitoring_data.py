#!/usr/bin/env python
"""
Data loader for Hamaarag monitoring database

This script loads data from a single CSV file containing all monitoring data into
the PostgreSQL database for the monitoring units and species observations schema.
It extracts and creates monitoring units, sites, points, campaigns, events, and
species observations from this single source file.

Usage:
    python load_monitoring_data.py --config config.json

Configuration file should contain:
    - Path to the single source CSV file
    - Mappings for data transformations

Database connection parameters are read from the .env file in the project root.

Dependencies:
    - pandas
    - psycopg2
    - uuid
    - python-dotenv
"""

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("monitoring_data_load.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def connect_to_db():
    """
    Connect to PostgreSQL database using environment variables

    Returns:
        connection: PostgreSQL database connection
    """
    try:
        # Load environment variables from .env file
        env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(dotenv_path=env_path)

        # Get database connection parameters from environment variables
        dbname = os.getenv("DB_NAME")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")

        connection = psycopg2.connect(
            dbname=dbname, user=user, password=password, host=host, port=port
        )
        logger.info("Successfully connected to the database")
        return connection
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        sys.exit(1)


def load_source_data(file_path):
    """
    Load data from the single source CSV file

    Args:
        file_path: Path to the single CSV file containing all monitoring data

    Returns:
        df: DataFrame containing all the data
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(
            f"Successfully loaded source data with {len(df)} rows and {len(df.columns)} columns"
        )
        return df
    except Exception as e:
        logger.error(f"Error loading source data: {e}")
        return None


def extract_monitoring_units(conn, source_df):
    """
    Extract and load monitoring units from the source data

    Args:
        conn: Database connection
        source_df: DataFrame containing source data

    Returns:
        units_df: DataFrame containing unit information with generated IDs
    """
    try:
        # Extract unique unit information
        units = source_df[["unit", "subunit"]].drop_duplicates()
        units.rename(
            columns={"unit": "unit_name", "subunit": "subunit_name"}, inplace=True
        )

        # Generate UUIDs for each unit
        units["unit_id"] = [str(uuid.uuid4()) for _ in range(len(units))]

        # Add description column (empty for now)
        units["description"] = None

        # Prepare data for insert
        data = [
            (row["unit_id"], row["unit_name"], row["subunit_name"], row["description"])
            for _, row in units.iterrows()
        ]

        # Insert data
        with conn.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO monitoring_unit (unit_id, unit_name, subunit_name, description)
                VALUES %s
                """,
                data,
            )

        conn.commit()
        logger.info(f"Successfully loaded {len(data)} monitoring units")

        # Return the dataframe with generated IDs
        return units

    except Exception as e:
        conn.rollback()
        logger.error(f"Error extracting and loading monitoring units: {e}")
        return None


def extract_monitoring_sites(conn, source_df, units_df):
    """
    Extract and load monitoring sites from the source data

    Args:
        conn: Database connection
        source_df: DataFrame containing source data
        units_df: DataFrame containing unit information with generated IDs

    Returns:
        sites_df: DataFrame containing site information with generated IDs
    """
    try:
        # Extract unique site information
        sites = source_df[["unit", "subunit", "site"]].drop_duplicates()
        sites.rename(
            columns={
                "unit": "unit_name",
                "subunit": "subunit_name",
                "site": "site_name",
            },
            inplace=True,
        )

        # Merge with units_df to get unit_id
        sites = pd.merge(
            sites,
            units_df[["unit_name", "subunit_name", "unit_id"]],
            on=["unit_name", "subunit_name"],
            how="left",
        )

        # Generate UUIDs for each site
        sites["site_id"] = [str(uuid.uuid4()) for _ in range(len(sites))]

        # Add description column (empty for now)
        sites["description"] = None

        # Prepare data for insert
        data = [
            (row["site_id"], row["unit_id"], row["site_name"], row["description"])
            for _, row in sites.iterrows()
        ]

        # Insert data
        with conn.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO monitoring_site (site_id, unit_id, site_name, description)
                VALUES %s
                """,
                data,
            )

        conn.commit()
        logger.info(f"Successfully loaded {len(data)} monitoring sites")

        # Return the dataframe with generated IDs
        return sites

    except Exception as e:
        conn.rollback()
        logger.error(f"Error extracting and loading monitoring sites: {e}")
        return None


def extract_monitoring_points(conn, source_df, units_df, sites_df):
    """
    Extract and load monitoring points from the source data

    Args:
        conn: Database connection
        source_df: DataFrame containing source data
        units_df: DataFrame containing unit information with generated IDs
        sites_df: DataFrame containing site information with generated IDs

    Returns:
        points_df: DataFrame containing point information with generated IDs
    """
    try:
        # Extract unique point information
        points = source_df[
            ["unit", "subunit", "site", "point_name", "habitat", "plot_coord"]
        ].drop_duplicates()
        points.rename(
            columns={
                "unit": "unit_name",
                "subunit": "subunit_name",
                "site": "site_name",
                "habitat": "habitat_type",
                "plot_coord": "coordinates",
            },
            inplace=True,
        )

        # Merge with units_df to get unit_id
        points = pd.merge(
            points,
            units_df[["unit_name", "subunit_name", "unit_id"]],
            on=["unit_name", "subunit_name"],
            how="left",
        )

        # Merge with sites_df to get site_id
        points = pd.merge(
            points,
            sites_df[["unit_name", "subunit_name", "site_name", "site_id"]],
            on=["unit_name", "subunit_name", "site_name"],
            how="left",
        )

        # Generate UUIDs for each point
        points["point_id"] = [str(uuid.uuid4()) for _ in range(len(points))]

        # Extract latitude and longitude from coordinates
        # Assuming coordinates are in the format "latitude_longitude"
        points["latitude"] = points["coordinates"].apply(
            lambda x: float(x.split("_")[0]) if pd.notnull(x) else None
        )
        points["longitude"] = points["coordinates"].apply(
            lambda x: float(x.split("_")[1]) if pd.notnull(x) else None
        )

        # Handle habitat_type conversions if needed
        # This depends on the specific values in your data and enum types in the database
        # For now, we'll use the values as-is

        # Add optional fields
        points["agriculture"] = None
        points["settlements"] = None
        points["dunes"] = None
        points["land_use"] = None
        points["notes"] = None

        # Prepare data for insert
        data = [
            (
                row["point_id"],
                row["unit_id"],
                row["site_id"],
                row["point_name"],
                row["longitude"],
                row["latitude"],
                row["habitat_type"] if pd.notnull(row["habitat_type"]) else None,
                row["agriculture"],
                row["settlements"],
                row["dunes"],
                row["land_use"],
                row["notes"],
            )
            for _, row in points.iterrows()
        ]

        # Insert data
        with conn.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO monitoring_point (
                    point_id, unit_id, site_id, point_name, longitude, latitude, 
                    habitat_type, agriculture, settlements, dunes, land_use, notes
                )
                VALUES %s
                """,
                data,
            )

        conn.commit()
        logger.info(f"Successfully loaded {len(data)} monitoring points")

        # Return the dataframe with generated IDs
        return points

    except Exception as e:
        conn.rollback()
        logger.error(f"Error extracting and loading monitoring points: {e}")
        return None


def extract_monitoring_campaigns(conn, source_df):
    """
    Extract and load monitoring campaigns from the source data

    Args:
        conn: Database connection
        source_df: DataFrame containing source data

    Returns:
        campaigns_df: DataFrame containing campaign information with generated IDs
    """
    try:
        # Extract unique campaign information
        campaigns = source_df[["campaign", "year"]].drop_duplicates()
        campaigns.rename(columns={"campaign": "campaign_code"}, inplace=True)

        # Generate UUIDs for each campaign
        campaigns["campaign_id"] = [str(uuid.uuid4()) for _ in range(len(campaigns))]

        # Add start_year and end_year (using year as both for now)
        campaigns["start_year"] = campaigns["year"]
        campaigns["end_year"] = campaigns["year"]

        # Add description column (empty for now)
        campaigns["description"] = None

        # Prepare data for insert
        data = [
            (
                row["campaign_id"],
                row["campaign_code"],
                row["start_year"],
                row["end_year"],
                row["description"],
            )
            for _, row in campaigns.iterrows()
        ]

        # Insert data
        with conn.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO monitoring_campaign (
                    campaign_id, campaign_code, start_year, end_year, description
                )
                VALUES %s
                """,
                data,
            )

        conn.commit()
        logger.info(f"Successfully loaded {len(data)} monitoring campaigns")

        # Return the dataframe with generated IDs
        return campaigns

    except Exception as e:
        conn.rollback()
        logger.error(f"Error extracting and loading monitoring campaigns: {e}")
        return None


def extract_monitoring_events(conn, source_df, campaigns_df, points_df):
    """
    Extract and load monitoring events from the source data

    Args:
        conn: Database connection
        source_df: DataFrame containing source data
        campaigns_df: DataFrame containing campaign information with generated IDs
        points_df: DataFrame containing point information with generated IDs

    Returns:
        events_df: DataFrame containing event information with generated IDs
    """
    try:
        # Extract event information (unique combinations of campaign, year, season, and point)
        events = source_df[
            ["campaign", "year", "season", "unit", "subunit", "site", "point_name"]
        ].drop_duplicates()
        events.rename(columns={"campaign": "campaign_code"}, inplace=True)

        # Merge with campaigns_df to get campaign_id
        events = pd.merge(
            events,
            campaigns_df[["campaign_code", "year", "campaign_id"]],
            on=["campaign_code", "year"],
            how="left",
        )

        # Merge with points_df to get point_id
        events = pd.merge(
            events,
            points_df[
                ["unit_name", "subunit_name", "site_name", "point_name", "point_id"]
            ],
            left_on=["unit", "subunit", "site", "point_name"],
            right_on=["unit_name", "subunit_name", "site_name", "point_name"],
            how="left",
        )

        # Generate UUIDs for each event
        events["event_id"] = [str(uuid.uuid4()) for _ in range(len(events))]

        # Add event_date (using year and season to create an approximate date)
        def get_date_from_year_season(year, season):
            if season == "Spring":
                return f"{year}-04-15"  # Mid April for Spring
            elif season == "Summer":
                return f"{year}-07-15"  # Mid July for Summer
            elif season == "Fall" or season == "Autumn":
                return f"{year}-10-15"  # Mid October for Fall
            elif season == "Winter":
                return f"{year}-01-15"  # Mid January for Winter
            else:
                return f"{year}-06-15"  # Default to mid-year

        events["event_date"] = events.apply(
            lambda row: get_date_from_year_season(row["year"], row["season"]), axis=1
        )

        # Add other fields with default/placeholder values
        events["start_time"] = "08:00:00"  # Default to 8 AM
        events["weather_code"] = "clear"  # Default to clear weather
        events["temperature"] = 25  # Default temperature
        events["wind"] = 1  # Default wind (light)
        events["clouds"] = 1  # Default clouds (few)
        events["precipitation"] = 0  # Default precipitation (none)
        events["disturbances"] = None  # No disturbances by default
        events["monitors_name"] = "Unknown"  # Unknown monitor
        events["notes"] = None  # No notes

        # Prepare data for insert
        data = [
            (
                row["event_id"],
                row["campaign_id"],
                row["point_id"],
                row["event_date"],
                row["start_time"],
                row["weather_code"],
                row["temperature"],
                row["wind"],
                row["clouds"],
                row["precipitation"],
                row["disturbances"],
                row["monitors_name"],
                row["notes"],
            )
            for _, row in events.iterrows()
        ]

        # Insert data
        with conn.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO monitoring_event (
                    event_id, campaign_id, point_id, event_date, start_time,
                    weather_code, temperature, wind, clouds, precipitation,
                    disturbances, monitors_name, notes
                )
                VALUES %s
                """,
                data,
            )

        conn.commit()
        logger.info(f"Successfully loaded {len(data)} monitoring events")

        # Return the dataframe with generated IDs
        return events

    except Exception as e:
        conn.rollback()
        logger.error(f"Error extracting and loading monitoring events: {e}")
        return None


def get_taxon_mappings(conn):
    """
    Get mappings between taxon IDs and entity IDs from the database

    Args:
        conn: Database connection

    Returns:
        taxon_version_map: Dictionary mapping scientific names to taxon_version_id
        taxon_entity_map: Dictionary mapping scientific names to taxon_entity_id
    """
    taxon_version_map = {}
    taxon_entity_map = {}

    try:
        with conn.cursor() as cursor:
            # Query to get taxon version IDs by scientific name
            cursor.execute(
                """
                SELECT scientific_name, taxon_version_id 
                FROM taxon_version
                WHERE is_current = TRUE
            """
            )
            for row in cursor.fetchall():
                scientific_name, taxon_id = row
                taxon_version_map[scientific_name] = taxon_id

            # Query to get taxon entity IDs
            cursor.execute(
                """
                SELECT tv.scientific_name, tv.taxon_entity_id
                FROM taxon_version tv
                WHERE tv.is_current = TRUE
            """
            )
            for row in cursor.fetchall():
                scientific_name, entity_id = row
                taxon_entity_map[scientific_name] = entity_id

        logger.info(
            f"Retrieved {len(taxon_version_map)} taxon version mappings and {len(taxon_entity_map)} entity mappings"
        )
        return taxon_version_map, taxon_entity_map

    except Exception as e:
        logger.error(f"Error getting taxon mappings: {e}")
        return {}, {}


def extract_species_observations(conn, source_df, events_df, taxon_version_map):
    """
    Extract and load species observations from the source data

    Args:
        conn: Database connection
        source_df: DataFrame containing source data
        events_df: DataFrame containing event information with generated IDs
        taxon_version_map: Dictionary mapping scientific names to taxon_version_id

    Returns:
        observations_df: DataFrame containing observation information with generated IDs
    """
    try:
        # Create a unique key for events to join with source data
        events_df["event_key"] = events_df.apply(
            lambda row: f"{row['campaign_code']}_{row['year']}_{row['season']}_{row['point_name']}",
            axis=1,
        )

        # Create the same key in source data
        source_df["event_key"] = source_df.apply(
            lambda row: f"{row['campaign']}_{row['year']}_{row['season']}_{row['point_name']}",
            axis=1,
        )

        # Prepare observations data
        observations = source_df[
            [
                "SciName",
                "event_key",
                "first_five_mins",
                "radius_0_20",
                "radius_20_100",
                "radius_100_250",
                "radius_over_250",
                "is_interacting",
            ]
        ].copy()

        # Map scientific names to taxon_version_id
        observations["taxon_id"] = observations["SciName"].map(taxon_version_map)

        # Merge with events_df to get event_id
        observations = pd.merge(
            observations,
            events_df[["event_key", "event_id"]],
            on="event_key",
            how="left",
        )

        # Filter out rows with missing taxon_id or event_id
        observations = observations.dropna(subset=["taxon_id", "event_id"])

        # Generate UUIDs for each observation
        observations["observation_id"] = [
            str(uuid.uuid4()) for _ in range(len(observations))
        ]

        # Calculate count_under_250
        observations["count_under_250"] = observations.apply(
            lambda row: (row["radius_0_20"] or 0)
            + (row["radius_20_100"] or 0)
            + (row["radius_100_250"] or 0),
            axis=1,
        )

        # Add notes column
        observations["notes"] = None

        # Prepare data for insert
        data = [
            (
                row["observation_id"],
                row["event_id"],
                row["taxon_id"],
                row["first_five_mins"],
                row["radius_0_20"] if pd.notnull(row["radius_0_20"]) else 0,
                row["radius_20_100"] if pd.notnull(row["radius_20_100"]) else 0,
                row["radius_100_250"] if pd.notnull(row["radius_100_250"]) else 0,
                row["radius_over_250"] if pd.notnull(row["radius_over_250"]) else 0,
                row["count_under_250"],
                row["is_interacting"] if pd.notnull(row["is_interacting"]) else False,
                row["notes"],
            )
            for _, row in observations.iterrows()
        ]

        # Insert data
        with conn.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO species_observation (
                    observation_id, event_id, taxon_id, first_five_mins,
                    radius_0_20, radius_20_100, radius_100_250, radius_over_250,
                    count_under_250, is_interacting, notes
                )
                VALUES %s
                """,
                data,
            )

        conn.commit()
        logger.info(f"Successfully loaded {len(data)} species observations")

        # Return the dataframe with generated IDs
        return observations

    except Exception as e:
        conn.rollback()
        logger.error(f"Error extracting and loading species observations: {e}")
        return None


def extract_species_breeding_relationships(conn, source_df, units_df, taxon_entity_map):
    """
    Extract and load species breeding relationships from the source data

    Args:
        conn: Database connection
        source_df: DataFrame containing source data
        units_df: DataFrame containing unit information with generated IDs
        taxon_entity_map: Dictionary mapping scientific names to taxon_entity_id

    Returns:
        breeding_df: DataFrame containing breeding relationship information with generated IDs
    """
    try:
        # Extract unique combinations of species and units
        breeding = source_df[
            ["SciName", "unit", "subunit", "is_breeding"]
        ].drop_duplicates()
        breeding.rename(
            columns={"unit": "unit_name", "subunit": "subunit_name"}, inplace=True
        )

        # Map scientific names to taxon_entity_id
        breeding["taxon_id"] = breeding["SciName"].map(taxon_entity_map)

        # Merge with units_df to get unit_id
        breeding = pd.merge(
            breeding,
            units_df[["unit_name", "subunit_name", "unit_id"]],
            on=["unit_name", "subunit_name"],
            how="left",
        )

        # Filter out rows with missing taxon_id or unit_id
        breeding = breeding.dropna(subset=["taxon_id", "unit_id"])

        # Generate UUIDs for each relationship
        breeding["relationship_id"] = [str(uuid.uuid4()) for _ in range(len(breeding))]

        # Ensure is_breeding is boolean
        breeding["is_breeding"] = breeding["is_breeding"].fillna(False).astype(bool)

        # Add notes column
        breeding["notes"] = None

        # Prepare data for insert
        data = [
            (
                row["relationship_id"],
                row["unit_id"],
                row["taxon_id"],
                row["is_breeding"],
                row["notes"],
            )
            for _, row in breeding.iterrows()
        ]

        # Insert data
        with conn.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO species_breeding_relationship (
                    relationship_id, unit_id, taxon_id, is_breeding, notes
                )
                VALUES %s
                """,
                data,
            )

        conn.commit()
        logger.info(f"Successfully loaded {len(data)} species breeding relationships")

        # Return the dataframe with generated IDs
        return breeding

    except Exception as e:
        conn.rollback()
        logger.error(
            f"Error extracting and loading species breeding relationships: {e}"
        )
        return None


def main():
    """Main function to load data from a single CSV file into the database"""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Load monitoring data from a single CSV file"
    )
    parser.add_argument("--config", required=True, help="Path to configuration file")
    args = parser.parse_args()

    # Load configuration
    try:
        with open(args.config, "r") as config_file:
            config = json.load(config_file)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)

    # Connect to database
    conn = connect_to_db()

    try:
        # Load source data
        source_df = load_source_data(config["files"]["source_file"])
        if source_df is None:
            raise Exception("Failed to load source data")

        # Get taxon mappings
        taxon_version_map, taxon_entity_map = get_taxon_mappings(conn)

        # Extract and load data in sequence based on dependencies
        units_df = extract_monitoring_units(conn, source_df)
        if units_df is None:
            raise Exception("Failed to extract and load monitoring units")

        sites_df = extract_monitoring_sites(conn, source_df, units_df)
        if sites_df is None:
            raise Exception("Failed to extract and load monitoring sites")

        points_df = extract_monitoring_points(conn, source_df, units_df, sites_df)
        if points_df is None:
            raise Exception("Failed to extract and load monitoring points")

        campaigns_df = extract_monitoring_campaigns(conn, source_df)
        if campaigns_df is None:
            raise Exception("Failed to extract and load monitoring campaigns")

        events_df = extract_monitoring_events(conn, source_df, campaigns_df, points_df)
        if events_df is None:
            raise Exception("Failed to extract and load monitoring events")

        observations_df = extract_species_observations(
            conn, source_df, events_df, taxon_version_map
        )
        if observations_df is None:
            raise Exception("Failed to extract and load species observations")

        breeding_df = extract_species_breeding_relationships(
            conn, source_df, units_df, taxon_entity_map
        )
        if breeding_df is None:
            raise Exception("Failed to extract and load species breeding relationships")

        logger.info("All data extracted and loaded successfully!")

    except Exception as e:
        logger.error(f"Error in data extraction and loading process: {e}")
        conn.close()
        sys.exit(1)

    # Close the connection
    conn.close()


if __name__ == "__main__":
    main()
