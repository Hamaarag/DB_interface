#!/usr/bin/env python3
"""
Apply Manual Corrections Script for Bird Data

This script applies the manual corrections described in the Data Preparation Notes
to resolve coordinate discrepancies, point name issues, and weather/disturbance data.

Based on the corrections documented for the Abreed_and_non_breed dataset.
"""

import pandas as pd
import numpy as np
import argparse
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def apply_manual_corrections(input_file, output_file):
    """
    Apply manual corrections to the bird monitoring dataset.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output corrected CSV file
    """
    try:
        # Read the source data
        logger.info(f"Reading data from {input_file}")
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} rows")
        
        # Keep track of corrections applied
        correction_stats = {
            "coordinate_corrections": 0,
            "point_name_changes": 0,
            "weather_disturbance_fixes": 0,
            "rows_deleted": 0,
            "spelling_corrections": 0
        }
        
        # 1. Weather/Disturbance corrections
        logger.info("Applying weather and disturbance corrections...")
        harsh_weather_mask = df['disturbances'] == 'harsh_weather'
        if harsh_weather_mask.any():
            # Copy comment_disturbances to comment_weather (overwrite)
            df.loc[harsh_weather_mask, 'comment_weather'] = df.loc[harsh_weather_mask, 'comment_disturbances']
            # Set disturbances to empty string
            df.loc[harsh_weather_mask, 'disturbances'] = ''
            # Set weather_desc to 'windy.rain_bursts'
            df.loc[harsh_weather_mask, 'weather_desc'] = 'windy.rain_bursts'
            # Set comment_disturbances to empty string
            df.loc[harsh_weather_mask, 'comment_disturbances'] = ''
            
            correction_stats["weather_disturbance_fixes"] = harsh_weather_mask.sum()
            logger.info(f"Fixed {correction_stats['weather_disturbance_fixes']} harsh_weather records")
        
        # 2. Spelling corrections: Ein Yaacov -> Ein Yaakov
        logger.info("Applying spelling corrections...")
        spelling_columns = ['unit', 'subunit', 'site', 'point_name']
        for col in spelling_columns:
            if col in df.columns:
                mask = df[col].str.contains('Ein Yaacov', na=False)
                if mask.any():
                    df.loc[mask, col] = df.loc[mask, col].str.replace('Ein Yaacov', 'Ein Yaakov')
                    correction_stats["spelling_corrections"] += mask.sum()
          # 3. Delete Garrulus glandarius artifact (Beit Oren Far 9, 2017, no counts)
        logger.info("Removing Garrulus glandarius artifact...")
        artifact_mask = (
            (df['SciName'] == 'Garrulus glandarius') &
            (df['year'] == 2017) &
            (df['unit'] == 'Mediterranean Maquis') &
            (df['site'] == 'Beit Oren') &
            (df['point_name'] == 'Beit Oren Far 9') &
            (df['total_count'] == 1)  # The arbitrary count that was set for the artifact
        )
        if artifact_mask.any():
            df = df[~artifact_mask].copy()
            correction_stats["rows_deleted"] = artifact_mask.sum()
            logger.info(f"Deleted {correction_stats['rows_deleted']} Garrulus glandarius artifact rows")
        # 4. Specific coordinate and point name corrections
        logger.info("Applying specific coordinate and point name corrections...")
        
        # Define all corrections as a list of dictionaries
        corrections = [
            # 1. Beit Oren Far 9 new, 2015 - change to Near 3 for incorrect coordinates
            {
                'condition': (df['year'] == 2015) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Beit Oren') & (df['point_name'] == 'Beit Oren Far 9 new') & 
                           (abs(df['lat'] - 32.73293057) < 0.0001) & (abs(df['lon'] - 35.01422596) < 0.0001),
                'point_name': 'Beit Oren Near 3',
                'description': 'Beit Oren Far 9 new -> Near 3 (2015, incorrect coordinates that belong to Near 3)'
            },
            
            # 2. Beit Oren Far 7 -> Far 8 in 2017 (specific date and total count based)
            {
                'condition': (df['year'] == 2017) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Beit Oren') & 
                           (df['point_name'] == 'Beit Oren Far 7') & 
                           (df['date'].str.contains('2017-05-30', na=False)) &
                           (
                               ((df['SciName'] == 'Curruca melanocephala') & (df['total_count'] == 2)) |
                               ((df['SciName'] == 'Corvus cornix') & (df['total_count'] == 1)) |
                               ((df['SciName'] == 'Garrulus glandarius') & (df['total_count'] == 4)) |
                               ((df['SciName'] == 'Clamator glandarius') & (df['total_count'] == 1)) |
                               ((df['SciName'] == 'Turdus merula') & (df['total_count'] == 3)) |
                               ((df['SciName'] == 'Streptopelia decaocto') & (df['total_count'] == 1))
                           ),
                'point_name': 'Beit Oren Far 8',
                'coordinates': (32.729000, 35.015731),  # Coordinates from Data Preparation Notes
                'time': '08:16:00',
                'description': 'Beit Oren Far 7 -> Far 8 correction for specific species with specific counts on 2017-05-30'
            },            
            # 3. Point name changes with 'a' suffix for 2012 points
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Beit Oren') & (df['point_name'] == 'Beit Oren Far 8'),
                'point_name': 'Beit Oren Far 8a',
                'description': 'Beit Oren Far 8 -> Far 8a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Kerem Maharal') & (df['point_name'] == 'Kerem Maharal Far 4'),
                'point_name': 'Kerem Maharal Far 4a',
                'description': 'Kerem Maharal Far 4 -> Far 4a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Kerem Maharal') & (df['point_name'] == 'Kerem Maharal Near 2'),
                'point_name': 'Kerem Maharal Near 2a',
                'description': 'Kerem Maharal Near 2 -> Near 2a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Kerem Maharal') & (df['point_name'] == 'Kerem Maharal Near 3'),
                'point_name': 'Kerem Maharal Near 2',
                'description': 'Kerem Maharal Near 3 -> Near 2 (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Nir Etzion') & (df['point_name'] == 'Nir Etzion Near 3'),
                'point_name': 'Nir Etzion Near 1',
                'description': 'Nir Etzion Near 3 -> Near 1 (2012 typo fix)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Nir Etzion') & (df['point_name'] == 'Nir Etzion Far 4'),
                'point_name': 'Nir Etzion Far 4a',
                'description': 'Nir Etzion Far 4 -> Far 4a (2012)'
            },            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Ofer') & (df['point_name'] == 'Ofer Far 5'),
                'point_name': 'Ofer Far 5a',
                'description': 'Ofer Far 5 -> Far 5a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Ofer') & (df['point_name'] == 'Ofer Far 6'),
                'point_name': 'Ofer Far 6a',
                'description': 'Ofer Far 6 -> Far 6a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Ofer') & (df['point_name'] == 'Ofer Near 2'),
                'point_name': 'Ofer Near 1',
                'description': 'Ofer Near 2 -> Near 1 (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Ofer') & (df['point_name'] == 'Ofer Near 3'),
                'point_name': 'Ofer Near 2',
                'description': 'Ofer Near 3 -> Near 2 (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Ofer') & (df['point_name'] == 'Ofer Near 4'),
                'point_name': 'Ofer Near 3',
                'description': 'Ofer Near 4 -> Near 3 (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Yagur') & (df['point_name'] == 'Yagur Far 4'),
                'point_name': 'Yagur Far 4a',
                'description': 'Yagur Far 4 -> Far 4a (2012)'
            },
            {
                'condition': (df['year'] == 2015) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Yagur') & (df['point_name'] == 'Yagur Far 4 new'),
                'point_name': 'Yagur Far 4b',
                'description': 'Yagur Far 4 new -> Far 4b (2015)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Yagur') & (df['point_name'] == 'Yagur Far 5'),
                'point_name': 'Yagur Far 5a',
                'description': 'Yagur Far 5 -> Far 5a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Yagur') & (df['point_name'] == 'Yagur Far 6'),
                'point_name': 'Yagur Far 6a',
                'description': 'Yagur Far 6 -> Far 6a (2012)'
            },
            
            # Abirim and Goren 2017 coordinate corrections (copy from other years)
            # Note: We'll need to find coordinates from other years for these points
              # Ein Yaakov corrections
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Ein Yaakov') & (df['point_name'] == 'Ein Yaakov Far 3'),
                'point_name': 'Ein Yaakov Far 3a',
                'description': 'Ein Yaakov Far 3 -> Far 3a (2012)'
            },
            {
                'condition': (df['year'] == 2015) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Ein Yaakov') & (df['point_name'] == 'Ein Yaakov Far 2 new'),
                'point_name': 'Ein Yaakov Far 21',
                'description': 'Ein Yaakov Far 2 new -> Far 21 (2015)'
            },
            
            # Goren corrections
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Goren') & (df['point_name'] == 'Goren Far 3'),
                'point_name': 'Goren Far 3a',
                'description': 'Goren Far 3 -> Far 3a (2012)'
            },
            
            # Iftach corrections
            {
                'condition': ((df['year'] == 2015) | (df['year'] == 2017)) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Iftach') & (df['point_name'] == 'Iftach Far 21'),
                'point_name': 'Iftach Far 22',
                'description': 'Iftach Far 21 -> Far 22 (2015, 2017)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Iftach') & (df['point_name'] == 'Iftach Far 3'),
                'point_name': 'Iftach Far 3a',
                'description': 'Iftach Far 3 -> Far 3a (2012)'
            },
            {
                'condition': (df['year'] == 2015) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Iftach') & (df['point_name'] == 'Iftach Far 4'),
                'point_name': 'Iftach Far 4a',
                'description': 'Iftach Far 4 -> Far 4a (2015)'
            },
            
            # Kfar Shamai corrections
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Kfar Shamai') & (df['point_name'] == 'Kfar Shamai Near 2') & 
                           (abs(df['lat'] - 32.94988) < 0.0001) & (abs(df['lon'] - 35.45682) < 0.0001),
                'point_name': 'Kfar Shamai Near 1',
                'description': 'Kfar Shamai Near 2 -> Near 1 (2012, specific coordinates)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Kfar Shamai') & (df['point_name'] == 'Kfar Shamai Far 1') & 
                           (abs(df['lat'] - 32.96506) < 0.0001) & (abs(df['lon'] - 35.45921) < 0.0001),
                'point_name': 'Kfar Shamai Far 1a',
                'description': 'Kfar Shamai Far 1 -> Far 1a (2012, coordinates 35.45921, 32.96506)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Kfar Shamai') & (df['point_name'] == 'Kfar Shamai Far 1') & 
                           (abs(df['lat'] - 32.9523) < 0.0001) & (abs(df['lon'] - 35.46524) < 0.0001),
                'point_name': 'Kfar Shamai Far 1b',
                'description': 'Kfar Shamai Far 1 -> Far 1b (2012, coordinates 35.46524, 32.9523)'
            },
            
            # Aderet corrections
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Aderet') & (df['point_name'] == 'Aderet Far 4'),
                'point_name': 'Aderet Far 4a',
                'description': 'Aderet Far 4 -> Far 4a (2012)'
            },
            
            # Givat Yearim corrections
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Givat Yearim') & (df['point_name'] == 'Givat Yearim Far 6'),
                'point_name': 'Givat Yearim Far 6a',
                'description': 'Givat Yearim Far 6 -> Far 6a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Givat Yearim') & (df['point_name'] == 'Givat Yearim Far 2'),
                'point_name': 'Givat Yearim Far 2a',
                'description': 'Givat Yearim Far 2 -> Far 2a (2012)'
            },
            
            # Givat Yeshayahu corrections
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Givat Yeshayahu') & (df['point_name'] == 'Givat Yeshayahu Far 3'),
                'point_name': 'Givat Yeshayahu Far 3a',
                'description': 'Givat Yeshayahu Far 3 -> Far 3a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Givat Yeshayahu') & (df['point_name'] == 'Givat Yeshayahu Far 4'),
                'point_name': 'Givat Yeshayahu Far 4a',
                'description': 'Givat Yeshayahu Far 4 -> Far 4a (2012)'
            },
            
            # Ramat Raziel corrections
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Ramat Raziel') & (df['point_name'] == 'Ramat Raziel Far 1'),
                'point_name': 'Ramat Raziel Far 1a',
                'description': 'Ramat Raziel Far 1 -> Far 1a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Ramat Raziel') & (df['point_name'] == 'Ramat Raziel Far 3'),
                'point_name': 'Ramat Raziel Far 3a',
                'description': 'Ramat Raziel Far 3 -> Far 3a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Ramat Raziel') & (df['point_name'] == 'Ramat Raziel Near 2'),
                'point_name': 'Ramat Raziel Near 1',
                'description': 'Ramat Raziel Near 2 -> Near 1 (2012)'
            },
            
            # Zuriel correction
            {
                'condition': (df['year'] == 2017) & (df['unit'] == 'Planted Conifer Forest') & (df['site'] == 'Zuriel') & (df['point_name'] == 'Zuriel KKL Plantings 1'),
                'point_name': 'Zuriel KKL Plantings 1a',
                'description': 'Zuriel KKL Plantings 1 -> 1a (2017)'
            },
            
            # Arid South points - Ein Yahav
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Arid South') & (df['site'] == 'Ein Yahav') & (df['point_name'] == 'Ein Yahav Far 1'),
                'point_name': 'Ein Yahav Far 1a',
                'description': 'Ein Yahav Far 1 -> Far 1a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Arid South') & (df['site'] == 'Ein Yahav') & (df['point_name'] == 'Ein Yahav Far 3'),
                'point_name': 'Ein Yahav Far 3a',
                'description': 'Ein Yahav Far 3 -> Far 3a (2012)'
            },
            
            # Paran
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Arid South') & (df['site'] == 'Paran') & (df['point_name'] == 'Paran Far 1'),
                'point_name': 'Paran Far 1a',
                'description': 'Paran Far 1 -> Far 1a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Arid South') & (df['site'] == 'Paran') & (df['point_name'] == 'Paran Far 2'),
                'point_name': 'Paran Far 2a',
                'description': 'Paran Far 2 -> Far 2a (2012)'
            },
            
            # Yotvata
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Arid South') & (df['site'] == 'Yotvata') & (df['point_name'] == 'Yotvata Near 1'),
                'point_name': 'Yotvata Near 1a',
                'description': 'Yotvata Near 1 -> Near 1a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Arid South') & (df['site'] == 'Yotvata') & (df['point_name'] == 'Yotvata Near 2'),
                'point_name': 'Yotvata Near 2a',
                'description': 'Yotvata Near 2 -> Near 2a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Arid South') & (df['site'] == 'Yotvata') & (df['point_name'] == 'Yotvata Near 3'),
                'point_name': 'Yotvata Near 3a',
                'description': 'Yotvata Near 3 -> Near 3a (2012)'
            },
            
            # Batha unit - Karei Deshe exchanges
            {
                'condition': ((df['year'] == 2014) | (df['year'] == 2016)) & (df['unit'] == 'Herbaceous and Dwarf-Shrub Vegetation') & (df['site'] == 'Karei Deshe') & (df['point_name'] == 'Karei Deshe Near 1'),
                'point_name': 'Karei Deshe Near 3',
                'description': 'Karei Deshe Near 1 -> Near 3 (2014, 2016)'
            },
            {
                'condition': ((df['year'] == 2014) | (df['year'] == 2016)) & (df['unit'] == 'Herbaceous and Dwarf-Shrub Vegetation') & (df['site'] == 'Karei Deshe') & (df['point_name'] == 'Karei Deshe Near 3'),
                'point_name': 'Karei Deshe Near 1',
                'description': 'Karei Deshe Near 3 -> Near 1 (2014, 2016)'
            },
            
            # Med-Desert Transition Zone - Har Amasa exchanges
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean-Desert Transition Zone') & (df['site'] == 'Har Amasa') & (df['point_name'] == 'Har Amasa Near 3'),
                'point_name': 'Har Amasa Near 5',
                'description': 'Har Amasa Near 3 -> Near 5 (2012 exchange)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean-Desert Transition Zone') & (df['site'] == 'Har Amasa') & (df['point_name'] == 'Har Amasa Near 5'),
                'point_name': 'Har Amasa Near 3',
                'description': 'Har Amasa Near 5 -> Near 3 (2012 exchange)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean-Desert Transition Zone') & (df['site'] == 'Har Amasa') & (df['point_name'] == 'Har Amasa Far 2'),
                'point_name': 'Har Amasa Far 2a',
                'description': 'Har Amasa Far 2 -> Far 2a (2012)'
            },
            
            # Lahav corrections
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean-Desert Transition Zone') & (df['site'] == 'Lahav') & (df['point_name'] == 'Lahav Far 2'),
                'point_name': 'Lahav Far 11',
                'description': 'Lahav Far 2 -> Far 11 (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean-Desert Transition Zone') & (df['site'] == 'Lahav') & (df['point_name'] == 'Lahav Far 3'),
                'point_name': 'Lahav Far 3a',
                'description': 'Lahav Far 3 -> Far 3a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean-Desert Transition Zone') & (df['site'] == 'Lahav') & (df['point_name'] == 'Lahav Near 4'),
                'point_name': 'Lahav Near 4a',
                'description': 'Lahav Near 4 -> Near 4a (2012)'
            },
            
            # Lehavim corrections
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean-Desert Transition Zone') & (df['site'] == 'Lehavim') & (df['point_name'] == 'Lehavim Far 2'),
                'point_name': 'Lehavim Far 2a',
                'description': 'Lehavim Far 2 -> Far 2a (2012)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean-Desert Transition Zone') & (df['site'] == 'Lehavim') & (df['point_name'] == 'Lehavim Near 1'),
                'point_name': 'Lehavim Near 3',
                'description': 'Lehavim Near 1 -> Near 3 (2012 exchange)'
            },
            {
                'condition': (df['year'] == 2012) & (df['unit'] == 'Mediterranean-Desert Transition Zone') & (df['site'] == 'Lehavim') & (df['point_name'] == 'Lehavim Near 3'),
                'point_name': 'Lehavim Near 1',
                'description': 'Lehavim Near 3 -> Near 1 (2012 exchange)'
            },
            {
                'condition': (df['year'] == 2014) & (df['unit'] == 'Mediterranean-Desert Transition Zone') & (df['site'] == 'Lehavim') & (df['point_name'] == 'Lehavim Near 6') & 
                           (abs(df['lat'] - 31.36837) < 0.0001) & (abs(df['lon'] - 34.82344) < 0.0001),
                'point_name': 'Lehavim Near 5',
                'description': 'Lehavim Near 6 -> Near 5 (2014, mislabeled)'
            },
            
            # Additional corrections
            {
                'condition': (df['year'] == 2015) & (df['unit'] == 'Mediterranean Maquis') & (df['site'] == 'Nir Etzion') & (df['point_name'] == 'Nir ezion Far 1 new'),
                'point_name': 'Nir Etzion Far 1 new',
                'description': 'Nir ezion Far 1 new -> Nir Etzion Far 1 new (2015 spelling)'
            }
        ]
          # Apply each correction
        for correction in corrections:
            mask = correction['condition']
            if mask.any():
                rows_affected = mask.sum()
                
                # Apply point name change if specified
                if 'point_name' in correction:
                    df.loc[mask, 'point_name'] = correction['point_name']
                    correction_stats["point_name_changes"] += rows_affected
                    logger.info(f"Applied point name correction: {correction['description']} - {rows_affected} rows")
                
                # Apply coordinate change if specified
                if 'coordinates' in correction:
                    lat, lon = correction['coordinates']
                    df.loc[mask, 'lat'] = round(lat, 6)
                    df.loc[mask, 'lon'] = round(lon, 6)
                    correction_stats["coordinate_corrections"] += rows_affected
                    logger.info(f"Applied coordinate correction: {correction['description']} - {rows_affected} rows")                
                # Apply time change if specified
                if 'time' in correction:
                    df.loc[mask, 'time'] = correction['time']
                    logger.info(f"Applied time correction: {correction['description']} - {rows_affected} rows")
            else:
                # Raise error if no rows match the correction condition
                raise ValueError(f"No rows found matching correction condition: {correction['description']}")
                logger.error(f"❌ CORRECTION FAILED: {correction['description']} - No matching rows found")        # 5. Point name corrections - Iftach Near 1 to Near 2 (misnamed)
        logger.info("Applying point name correction for Iftach Near 1 misnamed points...")
        iftach_near1_mask = (
            (df['unit'] == 'Mediterranean Maquis') &
            (df['site'] == 'Iftach') &
            (df['point_name'] == 'Iftach Near 1') &
            (df['year'].isin([2017, 2019, 2021])) &
            (abs(df['lat'] - 33.127499) < 0.000001) &
            (abs(df['lon'] - 35.549154) < 0.000001)
        )
        
        if iftach_near1_mask.any():
            df.loc[iftach_near1_mask, 'point_name'] = 'Iftach Near 2'
            rows_affected = iftach_near1_mask.sum()
            correction_stats["point_name_changes"] += rows_affected
            logger.info(f"Changed misnamed Iftach Near 1 to Iftach Near 2: {rows_affected} rows")
        else:
            raise ValueError("No rows found for Iftach Near 1 with coordinates (33.127499,35.549154) in 2017, 2019, 2021 - correction condition not met")
        
        # 6. Special case: Copy coordinates from other years for 2017 Abirim and Goren points
        logger.info("Copying coordinates from other years for 2017 Uri Arad points...")
        
        # List of points that need coordinate copying (with their units)
        copy_coord_points = [
            ('Mediterranean Maquis', 'Abirim', 'Abirim Far 1'),
            ('Mediterranean Maquis', 'Abirim', 'Abirim Far 2'),
            ('Mediterranean Maquis', 'Abirim', 'Abirim Far 3'),
            ('Mediterranean Maquis', 'Goren', 'Goren Far 3'),
            ('Mediterranean Maquis', 'Goren', 'Goren Far 41'),
            ('Mediterranean Maquis', 'Goren', 'Goren Far 5'),
            ('Mediterranean Maquis', 'Goren', 'Goren Near 1')
        ]
        
        for unit, site, point_name in copy_coord_points:
            # Find coordinates from other years (not 2017)
            other_years_mask = (df['unit'] == unit) & (df['site'] == site) & (df['point_name'] == point_name) & (df['year'] != 2017)
            year_2017_mask = (df['unit'] == unit) & (df['site'] == site) & (df['point_name'] == point_name) & (df['year'] == 2017)
            
            if other_years_mask.any() and year_2017_mask.any():
                # Get most common coordinates from other years
                other_coords = df.loc[other_years_mask, ['lat', 'lon']].mode()
                if not other_coords.empty:
                    correct_lat = round(other_coords.iloc[0]['lat'], 6)
                    correct_lon = round(other_coords.iloc[0]['lon'], 6)
                    
                    df.loc[year_2017_mask, 'lat'] = correct_lat
                    df.loc[year_2017_mask, 'lon'] = correct_lon
                    
                    rows_affected = year_2017_mask.sum()
                    correction_stats["coordinate_corrections"] += rows_affected
                    logger.info(f"Copied coordinates for {unit} {site} {point_name} 2017: {rows_affected} rows")
        
        # 7. Fix longitude typo for Turdus merula in Ofer Far 6, 2019
        logger.info("Fixing Turdus merula longitude typo...")
        turdus_mask = (
            (df['SciName'] == 'Turdus merula') &
            (df['year'] == 2019) &
            (df['unit'] == 'Mediterranean Maquis') &
            (df['site'] == 'Ofer') &
            (df['point_name'] == 'Ofer Far 6')
        )
        
        if turdus_mask.any():
            # Get correct coordinates from other observations at the same point
            other_ofer_mask = (
                (df['unit'] == 'Mediterranean Maquis') &
                (df['site'] == 'Ofer') &
                (df['point_name'] == 'Ofer Far 6') &
                (df['year'] == 2019) &
                (~turdus_mask)
            )
            
            if other_ofer_mask.any():
                correct_coords = df.loc[other_ofer_mask, ['lat', 'lon']].mode()
                if not correct_coords.empty:
                    df.loc[turdus_mask, 'lat'] = round(correct_coords.iloc[0]['lat'], 6)
                    df.loc[turdus_mask, 'lon'] = round(correct_coords.iloc[0]['lon'], 6)
                    
                    rows_affected = turdus_mask.sum()
                    correction_stats["coordinate_corrections"] += rows_affected
                    logger.info(f"Fixed Turdus merula longitude typo: {rows_affected} rows")
        
        # Write the corrected data
        logger.info(f"Writing corrected data to {output_file}")
        df.to_csv(output_file, index=False)
        
        # Print summary statistics
        logger.info("=== MANUAL CORRECTIONS SUMMARY ===")
        logger.info(f"Total rows processed: {len(df)}")
        logger.info(f"Coordinate corrections applied: {correction_stats['coordinate_corrections']}")
        logger.info(f"Point name changes applied: {correction_stats['point_name_changes']}")
        logger.info(f"Weather/disturbance fixes applied: {correction_stats['weather_disturbance_fixes']}")
        logger.info(f"Spelling corrections applied: {correction_stats['spelling_corrections']}")
        logger.info(f"Rows deleted (artifacts): {correction_stats['rows_deleted']}")
        logger.info(f"✅ Manual corrections completed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during manual corrections: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Apply manual corrections to bird monitoring data"
    )
    parser.add_argument(
        "--input", 
        default="data/Abreed_and_non_breed_orig.csv",
        help="Input CSV file path (default: data/Abreed_and_non_breed_orig.csv)"
    )
    parser.add_argument(
        "--output",
        default="data/Abreed_and_non_breed_post_manual_fix_of_mult_coord.csv",
        help="Output CSV file path (default: data/Abreed_and_non_breed_post_manual_fix_of_mult_coord.csv)"
    )
    
    args = parser.parse_args()
    
    # Convert relative paths to absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up two levels from src/data_prep to get to the project root
    project_root = os.path.dirname(os.path.dirname(script_dir))
    
    # Handle relative paths properly
    if not os.path.isabs(args.input):
        # If it's a relative path, resolve it from the project root
        input_path = os.path.normpath(os.path.join(project_root, args.input))
    else:
        input_path = args.input
        
    if not os.path.isabs(args.output):
        # If it's a relative path, resolve it from the project root
        output_path = os.path.normpath(os.path.join(project_root, args.output))
    else:
        output_path = args.output
    
    try:
        success = apply_manual_corrections(input_path, output_path)
        
        if success:
            logger.info(f"Manual corrections completed successfully!")
            logger.info(f"Output file: {output_path}")
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to apply manual corrections: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
