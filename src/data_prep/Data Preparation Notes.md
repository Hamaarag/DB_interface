# Data Preparation Notes - Bird Data
Ron Chen  

## Overview and order of operations
This document outlines the steps taken to clean and prepare bird data for analysis, specifically focusing on the dataset `Abreed_and_non_breed_orig.csv`, which is an output of the script [prepare_bird_data_with_Z_filter.R](https://github.com/Hamaarag/SoN_2023_Birds/blob/551f38bf195208001256d8164b5684484d53a565/R/prepare_bird_data_with_Z_filter.R) used in SoN 2023 bird analysis. The data preparation process involved several scripts and manual corrections to ensure the accuracy and consistency of the data. The main steps included:  
1. **Multiple Coordinate Corrections**: Using `clean_coordinates.py` to resolve multiple coordinates per point. This script handled some of the discrepancies automatically (whatever is <100m from the closest point), while others required manual intervention.  
2. **Point Name Corrections**: Using `clean_multiple_point_names_per_location.py` to resolve multiple point names per location.  
3. **Disturbances and Weather Corrections**: Manually correcting disturbances and weather descriptions in the dataset.  

## Correction of multiple coordinates per point using `apply_manual_corrections.py`
This script was generated based on meticulous manual examination of the flagged point list as outputed by `clean_coordinates.py` which was run on the input file `Abreed_and_non_breed_orig.csv`.  

**Date:** 2025-06-23  
**Input file:** data/Abreed_and_non_breed_orig.csv  
**Cleaned output file:** data/Abreed_and_non_breed_post_manual_fix_of_mult_coord.csv  

The following manual corrections were made to sampling points (identified by unit-subunit-site-point_name) in Abreed_and_non_breed.csv (now named with the suffix `_orig`, hereafter 'Abreed_orig'), which contained multiple coordinate pairs, using the script `clean_coordinates.py`. The CSV contains bird data used for SoN 2023 bird analysis, from 2012 to 2021.
It should be noted that some of the listed corrections may also apply to succeeding years of the national monitoring program (e.g., the misnaming of Med Maquis Iftach Near 2 as Iftach Near 1).
As a general rule, if a discrepancy existed across years (e.g., point "A" had coordinates lat1,lon1 in years 2012 and 2014, and lat2,lon2 in years 2016 and 2020), I preferred making the corrections on the earlier years (accordingly, renaming 2012 and 2014 while keeping name for 2016 and 2020).

1. Med Maquis Beit Oren Far 9 new, 2015: this year-point combo shows two coordinate pairs: (35.01808285	32.74067667) and (35.01422596	32.73293057). The former are the correct coords for Far 9 new. The latter are the coords of Beit Oren Near 3, which is missing from Abreed_orig and was designated with the Hebrew point name (Title field in Fulcrum), "בית אורן". I changed Beit Oren Far 9 new to Beit Oren Near 3 for the latter coordinate pair in 2015. Time was not corrected. It should be noted that there is additional information - monitor's name (Uri Arad here), weather comments, disturbances, other comments - that is missing from Abreed_orig but exists in the raw data in Fulcrum.

2. Med Maquis Beit Oren Far in 2017:
	(1) has only two plots instead of three. Observations missing from Fulcrum, but start times exist (in Fulcrum; in Abreed_orig there is only the time of the Far 7 plot). Observations listed in separate file, `נתוני עופות 2017 אורי ערד.xlsx`. The latter also lists just two far plots, 7 and 9, but plot far 7 has two starting times. I compared Fulcrum start times with the obs xlsx file, and found that obs made on 30/5/2017 08:16 belong to Far 8, not Far 7. Corrected Abreed_orig by changing the following observations to point name = Beit Oren Far 8, coordinates = (35.015731	32.729000), and time = 08:16:00:
       - Curruca melanocephala - total count of 2
       - Corvus cornix - total count of 1
       - Garrulus glandarius - total count of 4
       - Clamator glandarius - total count of 1
       - Turdus merula - total count of 3
       - Streptopelia decaocto - total count of 1
	(2) Garrulus glandarius obs, which appears in Abreed_orig in Far 9, has no counts in the separate distance categories and was arbitrarily set to total count of 1, is in fact an artifact. deleted.
	(3) I identified the obs that were labeled with Far 7 but that belong to Far 8, by comparing to the separate xlsx obs file. labelled them with Far 8 and corrected their cords to match Far 8 in other years.

3. Med Maquis Beit Oren Far 8 in 2012: (32.7366,35.01536) which are the 2012 coordinates are not near any other point in the dataset, hence I label this point as Beit Oren Far 8a (new label).  
Similarly:  
 - Med Maquis Kerem Maharal Far 4 in 2012 --> Med Maquis Kerem Maharal Far 4a (new label)  
 - Med Maquis Kerem Maharal Near 2 in 2012 --> Med Maquis Kerem Maharal Near 2a (new label)
 - Med Maquis Kerem Maharal Near 3 in 2012 --> Med Maquis Kerem Maharal Near 2  
 - Med Maquis Nir Etzion Near 3 in 2012 --> Nir Etzion Near 1 (typo in one row that created a fourth plot in Nir Etzion Near 2012)
 - Med Maquis Nir Etzion Far 4 in 2012 --> Nir Etzion Far 4a (new label)  
 - Med Maquis Ofer Far 6 in 2012 --> Ofer Far 6a (new label)  
 - Med Maquis Ofer Far 5 in 2012 --> Ofer Far 5a (new label)
 - Med Maquis Ofer Near 2 in 2012 --> Near 1  
 - Med Maquis Ofer Near 3 in 2012 --> Near 2  
 - Med Maquis Ofer Near 4 in 2012 --> Near 3  
 - Med Maquis Yagur Far 4 in 2012 --> Far 4a  
 - Med Maquis Yagur Far 4 new in 2015 --> Far 4b (just rename)  
 - Med Maquis Yagur Far 5 in 2012 --> Far 5a  
 - Med Maquis Yagur Far 6 in 2012 --> Far 6a
 - Med Maquis Abirim Far 1,2,3 in 2017 --> something happened that year, Uri Arad was the monitor and he reported his observations in a separate xlsx file (see above), and apparently also the coordinates in Fulcrum are not precise. I copied the coordinates for these three points from the other years. Same for Med Maquis Goren Far 3, Goren Far 41, Goren Far 5 and Goren Near 1 in 2017.  
 - Points with the spelling Ein Yaacov --> Ein Yaakov  
 - Med Maquis Ein Yaakov Far 3 in 2012 --> Far 3a  
 - Med Maquis Ein Yaakov Far 2 new in 2015 --> Far 21 (join with existing label)  
 - Med Maquis Goren Far 3 in 2012 --> Far 3a  
 - Med Maquis Iftach Far 21 in 2015, 2017 --> Far 22 (to separate from 2019 and 2021 in which the point was moved adjacent to the dirt road; no documentation found to support this change in the yearly bird monitoring summary)  
 - Med Maquis Iftach Far 3 in 2012 --> Far 3a  
 - Med Maquis Iftach Far 4 in 2015 --> Far 4a  
 - Med Maquis Iftach Near 1 in 2017, 2019, 2021 coordinates (33.127499,35.549154) --> Iftach Near 2  (misnamed)
 - Med Maquis Kfar Shamai Near 2 in 2012 with coordinates (35.45682	32.94988) --> Kfar Shamai Near 1  
 - Med Maquis Kfar Shamai Far 1 in 2012 with coordinates (35.45921	32.96506) --> Kfar Shamai Far 1a  
 - Med Maquis Kfar Shamai Far 1 in 2012 with coordinates (35.46524	32.9523) --> Kfar Shamai Far 1b  
 - Med Maquis Aderet Far 4 in 2012 --> Aderet Far 4a  
 - Med Maquis Givat Yearim Far 6 in 2012 --> Far 6a  
 - Med Maquis Givat Yearim Far 2 in 2012 --> Far 2a  
 - Med Maquis Givat Yeshayahu Far 3 in 2012 --> Far 3a  
 - Med Maquis Givat Yeshayahu Far 4 in 2012 --> Far 4a  
 - Med Maquis Ramat Raziel Far 1 in 2012 --> Far 1a  
 - Med Maquis Ramat Raziel Far 3 in 2012 --> Far 3a  
 - Med Maquis Ramat Raziel Near 2 in 2012 --> Near 1 (joined with existing label)  
 - Planted Conifer Forest Zuriel KKL Plantings 1 in 2017 --> Zuriel KKL Plantings 1a. As mentioned above, monitored by Uri Arad, who probably did not reach the point but performed the count on the dirt road.
 - The following points in 2012 were renamed with the suffix 'a':  
    - Ein Yahav: Far 1, Far 3  
    - Paran: Far 1, Far 2
    - Yotvata: Near 1, Near 2, Near 3  
 - Batha unit, Karei Deshe Near 1 and Near 3 in 2014 and 2016 --> Near 3 and Near 1, respectively (somehow they were exchanged between 2016 and 2018)
 - Med-Desert Transition Zone unit, Har Amasa Near 3 and Near 5 in 2012 were exchanged  
 - Med-Desert Transition Zone unit, Har Amasa Far 2 in 2012 --> Far 2a  
 - Med-Desert Transition Zone unit, Lahav Far 2 in 2012 --> Far 11 (joined with existing label)  
 - Med-Desert Transition Zone unit, Lahav Far 3 in 2012 --> Far 3a  
 - Med-Desert Transition Zone unit, Lahav Near 4 in 2012 --> Near 4a  
 - Med-Desert Transition Zone unit, Lehavim Far 2 in 2012 --> Far 2a  
 - Med-Desert Transition Zone unit, Lehavim Near 1 and Near 3 in 2012 were exchanged  
 - Med-Desert Transition Zone Unit, Lehavim Near 6 in 2014 with coordinates (34.82344	31.36837) --> Near 5 (mislabeled as part of Near 6, essentially part of Near 5)

4. Med Maquis Nir ezion Far 1 new in 2015 --> Nir Etzion Far 1 new  
5. Lon typo in single observation of turdus merula in Med Maquis Ofer Far 6 in 2019 --> corrected to match rest of observations  

### Disturbances - weather discrepances

In addition to the coordinate corrections, I also made some manual corrections to the disturbances and weather descriptions in the dataset. The following changes were applied:  

For all records with the value 'harsh_weather' in the `disturbances` column:
 - `disturbances` set to blank
 - `weather_desc` set to 'windy.rain_bursts'
 - values from `comment_disturbances` were copied to `comment_weather`
 - `comment_disturbances` set to blank

## Automatic correction of multiple coordinates per point, using `clean_coordinates.py`

**Timestamp:** 2025-06-23 12:48:24
**Input file:** data/Abreed_and_non_breed_post_manual_fix_of_mult_coord.csv  
**Cleaned output file:** data/Abreed_and_non_breed_cleaned_mult_coord.csv  
**Log file:** src/data_prep/Abreed_and_non_breed_cleaned_mult_coord.md  
**Distance threshold:** 100.0 meters
**Coordinate precision:** 1e-6 degrees  

The script `clean_coordinates.py` was used to automatically correct multiple coordinates per point in the dataset. The script identified points with multiple coordinates and applied the following rules:
- If a point had multiple coordinates within 100 meters of each other, the closest coordinate was retained.
- If a point had multiple coordinates that were more than 100 meters apart, the point was flagged for manual review (see above).  

### PROCESSING NOTES

- All coordinates rounded to 1e-6 precision before analysis
- Original coordinates preserved as orig_lat, orig_lon fields
- Auto-correction uses coordinates from the most recent year
- Flagged discrepancies exported to: data/Abreed_and_non_breed_post_manual_fix_of_mult_coord_flagged_coordinates.csv
- Cleaned data exported to: data/Abreed_and_non_breed_cleaned_mult_coord.csv

### SUMMARY STATISTICS

- **Total rows processed:** 16803
- **Rows with valid coordinates:** 16803
- **Rows without coordinates:** 0
- **Unique point groups examined:** 609
- **Point groups with unique coordinates:** 542
- **Point groups auto-corrected:** 67
- **Point groups flagged for review:** 0
- **Total rows auto-corrected:** 2940
- **Total rows flagged for manual review:** 0

## Point Name Corrections Applied Using `clean_multiple_point_names_per_location.py`

**Date:** 2025-06-23 13:16:35
**Input file:** data\Abreed_and_non_breed_cleaned_mult_coord.csv
**Cleaned output file:** data\Abreed_and_non_breed_cleaned.csv
**Log file:** data/Abreed_and_non_breed_cleaned.md  

The script `clean_multiple_point_names_per_location.py` was used to resolve multiple point names per location in the dataset. The script applied the following rules:
 - For conflicts within the same unit and site, it automatically applies fixes by keeping
the most recent point name.
 - For conflicts across different units or sites, it flags
them for manual review.

### Summary

- **Total conflicts detected:** 104
- **Automatically fixed:** 52
- **Requiring manual review:** 0
- **Total rows affected:** 760
