# Data Preparation Notes - Bird Data
18/6/2025 Ron Chen  

## Resolving multiple coordinates per point, using `clean_coordinates.py`

The following corrections were made to sampling points (identified by unit-subunit-site-point_name) in Abreed_and_non_breed.csv (now named with the suffix `_orig`, hereafter 'Abreed_orig'), which contained multiple coordinate pairs, using the script `clean_coordinates.py`. The CSV contains bird data used for SoN 2023 bird analysis, from 2012 to 2021.
It should be noted that some of the listed corrections may also apply to succeeding years of the national monitoring program (e.g., the misnaming of Med Maquis Iftach Near 2 as Iftach Near 1).
As a general rule, if a discrepancy existed across years (e.g., point "A" had coordinates lat1,lon1 in years 2012 and 2014, and lat2,lon2 in years 2016 and 2020), I preferred making the corrections on the earlier years (accordingly, renaming while keeping the later years

1. Med Maquis Beit Oren Far 9 new, 2015: (35.01808285	32.74067667) are the correct coords. (35.01422596	32.73293057) are the cords of Beit Oren Near 3, which was designated with the Hebrew point name (Title field in Fulcrum), "בית אורן". Monitor's name was set to Uri Arad. It should be noted that there is additional information - weather comments, disturbances, other comments - that is missing from Abreed_and_non_breed.csv but exists in the raw data in Fulcrum.

2. Med Maquis Beit Oren Far in 2017:
	(1) has only two plots instead of three. Observations missing from Fulcrum, but start times exist. Observations listed in separate file, `נתוני עופות 2017 אורי ערד.xlsx`. The latter also lists just two far plots, 7 and 9, but plot far 7 has two starting times. I compared Fulcrum start times with the obs xlsx file, and found that obs made on 30/5/2017 08:16 belong to Far 8, not Far 7. Corrected the xlsx file.
	(2) Garrulus glandarius obs, which appears in Abreed_orig in Far 9 and has no counts, is an artifact. deleted.
	(3) I identified the obs that were labeled with Far 7 but that belong to Far 8, by comparing to the separate xlsx obs file. labelled them with Far 8 and corrected their cords to match Far 8 in other years.

3. Med Maquis Beit Oren Far 8 in 2012: (32.7366,35.01536) which are the 2012 coordinates are not near any other point in the dataset, hence I label this point as Beit Oren Far 8a (new label).  
Similarly:  
 - Med Maquis Kerem Maharal 4 in 2012 --> Med Maquis Kerem Maharal 4a (new label)  
 - Med Maquis Kerem Maharal Near 2 in 2012 --> Med Maquis Kerem Maharal Near 2a (new label)
 - Med Maquis Kerem Maharal Near 3 in 2012 --> Med Maquis Kerem Maharal Near 2  
 - Med Maquis Nir Etzion Near 3 in 2012 --> Nir Etzion Near 1 (typo in one row that created a fourth plot in Nir Etzion Near 2012)
 - Med Maquis Nir Etzion Far 4 in 2012 --> Nir Etzion Far 4a (new label)  
 - Med Maquis Ofer Far 6 in 2012 --> Ofer Far 6a (new label)  
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
6. In Med Maquis Yiftach Near 1 in 2017, 2019, 2021  

## Point Name Corrections Applied Using `clean_multiple_point_names_per_location.py`

**Date:** 2025-06-19 19:17:41  
**Input file:** data/Abreed_and_non_breed_cleaned_mult_coord.csv  
**Cleaned output file:** data/Abreed_and_non_breed_cleaned_mult_coord_point_names_cleaned.csv  

### Summary

- **Total conflicts detected:** 102  
- **Automatically fixed:** 51  
- **Requiring manual review:** 0  
- **Total rows affected:** 754  

### Automatic Corrections Applied

| Coordinates | Unit | Site | Old Point Name | New Point Name | Reason | Rows Affected |
|-------------|------|------|----------------|----------------|--------|---------------|
| 30.849710000000005,34.78768 | Negev Highlands | Sde Boker | Midrasha Near Slope 1 | Sde Boker Near Slope 1 | Most recent year: 2020 | 15 |
| 30.851910000000004,34.77508 | Negev Highlands | Sde Boker | Midrasha Near Slope 4 | Sde Boker Near Slope 4 | Most recent year: 2020 | 19 |
| 30.853280000000005,34.76617 | Negev Highlands | Sde Boker | Midrasha Far Wadi 5 | Sde Boker Far Wadi 5 | Most recent year: 2020 | 15 |
| 30.853600000000004,34.75744 | Negev Highlands | Sde Boker | Midrasha Far Slope 8 | Sde Boker Far Slope 8 | Most recent year: 2020 | 10 |
| 30.854670000000006,34.80234000000001 | Negev Highlands | Sde Boker | Midrasha Far Slope 9 | Sde Boker Far Slope 9 | Most recent year: 2020 | 7 |
| 30.856380000000005,34.78437 | Negev Highlands | Sde Boker | Midrasha Near Slope 3 | Sde Boker Near Slope 3 | Most recent year: 2020 | 14 |
| 30.856500000000004,34.79583 | Negev Highlands | Sde Boker | Midrasha Far Slope 2 | Sde Boker Far Slope 2 | Most recent year: 2020 | 9 |
| 30.863560000000003,34.7644 | Negev Highlands | Sde Boker | Midrasha Far Wadi 7 | Sde Boker Far Wadi 7 | Most recent year: 2020 | 8 |
| 30.864090000000004,34.773970000000006 | Negev Highlands | Sde Boker | Midrasha Far Wadi 6 | Sde Boker Far Wadi 6 | Most recent year: 2020 | 13 |
| 31.507520000000003,34.894960000000005 | Planted Conifer Forest | Amatzia | Amatzia 2 | Amatzia KKL Plantings 2 | Most recent year: 2021 | 6 |
| 31.507520000000003,34.894960000000005 | Planted Conifer Forest | Amatzia | Amatzia Far 2 | Amatzia KKL Plantings 2 | Most recent year: 2021 | 8 |
| 31.512450000000005,34.89349000000001 | Planted Conifer Forest | Amatzia | Amatzia 1 | Amatzia KKL Plantings 1 | Most recent year: 2021 | 12 |
| 31.512450000000005,34.89349000000001 | Planted Conifer Forest | Amatzia | Amatzia Far 1 | Amatzia KKL Plantings 1 | Most recent year: 2021 | 8 |
| 31.514400000000006,34.89826000000001 | Planted Conifer Forest | Amatzia | Amatzia 3 | Amatzia KKL Plantings 3 | Most recent year: 2021 | 10 |
| 31.514400000000006,34.89826000000001 | Planted Conifer Forest | Amatzia | Amatzia Far 3 | Amatzia KKL Plantings 3 | Most recent year: 2021 | 6 |
| 31.665400000000005,34.91740000000001 | Planted Conifer Forest | Givat Yeshayahu | Givat Yeshaayahu 3 | Givat Yeshayahu KKL Forest 3 | Most recent year: 2021 | 7 |
| 31.665400000000005,34.91740000000001 | Planted Conifer Forest | Givat Yeshayahu | Givat Yeshayahu Far 3 | Givat Yeshayahu KKL Forest 3 | Most recent year: 2021 | 8 |
| 31.665400000000005,34.91740000000001 | Planted Conifer Forest | Givat Yeshayahu | Givat Yeshayahu KKL Plantings 3 | Givat Yeshayahu KKL Forest 3 | Most recent year: 2021 | 39 |
| 31.667740000000006,34.92544 | Planted Conifer Forest | Givat Yeshayahu | Givat Yeshaayahu 2 | Givat Yeshayahu KKL Forest 2 | Most recent year: 2021 | 7 |
| 31.667740000000006,34.92544 | Planted Conifer Forest | Givat Yeshayahu | Givat Yeshayahu Far 2 | Givat Yeshayahu KKL Forest 2 | Most recent year: 2021 | 7 |
| 31.667740000000006,34.92544 | Planted Conifer Forest | Givat Yeshayahu | Givat Yeshayahu KKL Plantings 2 | Givat Yeshayahu KKL Forest 2 | Most recent year: 2021 | 28 |
| 31.670440000000006,34.920660000000005 | Planted Conifer Forest | Givat Yeshayahu | Givat Yeshaayahu 1 | Givat Yeshayahu KKL Forest 1 | Most recent year: 2021 | 7 |
| 31.670440000000006,34.920660000000005 | Planted Conifer Forest | Givat Yeshayahu | Givat Yeshayahu Far 1 | Givat Yeshayahu KKL Forest 1 | Most recent year: 2021 | 6 |
| 31.670440000000006,34.920660000000005 | Planted Conifer Forest | Givat Yeshayahu | Givat Yeshayahu KKL Plantings 1 | Givat Yeshayahu KKL Forest 1 | Most recent year: 2021 | 37 |
| 31.671450000000004,34.988020000000006 | Planted Conifer Forest | Aderet | Aderet 3 | Aderet KKL Plantings 3 | Most recent year: 2021 | 7 |
| 31.671450000000004,34.988020000000006 | Planted Conifer Forest | Aderet | Aderet Far 3 | Aderet KKL Plantings 3 | Most recent year: 2021 | 7 |
| 31.675780000000003,34.98669 | Planted Conifer Forest | Aderet | Aderet 2 | Aderet KKL Plantings 2 | Most recent year: 2021 | 6 |
| 31.675780000000003,34.98669 | Planted Conifer Forest | Aderet | Aderet Far 2 | Aderet KKL Plantings 2 | Most recent year: 2021 | 7 |
| 31.678670000000004,34.98154 | Planted Conifer Forest | Aderet | Aderet 1 | Aderet KKL Plantings 1 | Most recent year: 2021 | 8 |
| 31.678670000000004,34.98154 | Planted Conifer Forest | Aderet | Aderet Far 1 | Aderet KKL Plantings 1 | Most recent year: 2021 | 9 |
| 31.774930000000005,35.09886 | Planted Conifer Forest | Eitanim | Eitanim 3 | Eitanim KKL Plantings 3 | Most recent year: 2021 | 5 |
| 31.774930000000005,35.09886 | Planted Conifer Forest | Eitanim | Eitanim Far 3 | Eitanim KKL Plantings 3 | Most recent year: 2021 | 6 |
| 31.778760000000005,35.109350000000006 | Planted Conifer Forest | Eitanim | Eitanim 1 | Eitanim KKL Plantings 1 | Most recent year: 2021 | 7 |
| 31.778760000000005,35.109350000000006 | Planted Conifer Forest | Eitanim | Eitanim Far 1 | Eitanim KKL Plantings 1 | Most recent year: 2021 | 6 |
| 31.779090000000004,35.10360000000001 | Planted Conifer Forest | Eitanim | Eitanim 2 | Eitanim KKL Plantings 2 | Most recent year: 2021 | 6 |
| 31.779090000000004,35.10360000000001 | Planted Conifer Forest | Eitanim | Eitanim Far 2 | Eitanim KKL Plantings 2 | Most recent year: 2021 | 4 |
| 31.783780000000004,35.020570000000006 | Planted Conifer Forest | Eshtaol | Eshtaol 4 | Eshtaol KKL Plantings 4 | Most recent year: 2021 | 7 |
| 31.783780000000004,35.020570000000006 | Planted Conifer Forest | Eshtaol | Eshtaol Far 4 | Eshtaol KKL Plantings 4 | Most recent year: 2021 | 6 |
| 31.786940000000005,35.02194000000001 | Planted Conifer Forest | Eshtaol | Eshtaol Far 3 | Eshtaol 3 | Most recent year: 2015 | 5 |
| 31.790750000000006,35.019960000000005 | Planted Conifer Forest | Eshtaol | Eshtaol 1 | Eshtaol KKL Plantings 1 | Most recent year: 2021 | 3 |
| 31.790750000000006,35.019960000000005 | Planted Conifer Forest | Eshtaol | Eshtaol Far 1 | Eshtaol KKL Plantings 1 | Most recent year: 2021 | 5 |
| 32.58547000000001,35.014160000000004 | Planted Conifer Forest | Bat Shlomo | Bat Shlomo 2 | Bat Shlomo KKL Plantings 2 | Most recent year: 2021 | 7 |
| 32.58547000000001,35.014160000000004 | Planted Conifer Forest | Bat Shlomo | Bat Shlomo Far 2 | Bat Shlomo KKL Plantings 2 | Most recent year: 2021 | 8 |
| 32.58717000000001,35.010540000000006 | Planted Conifer Forest | Bat Shlomo | Bat Shlomo 3 | Bat Shlomo KKL Plantings 3 | Most recent year: 2021 | 11 |
| 32.59044000000001,35.01371 | Planted Conifer Forest | Bat Shlomo | Bat Shlomo 1 | Bat Shlomo KKL Plantings 1 | Most recent year: 2021 | 12 |
| 32.613670000000006,35.118300000000005 | Planted Conifer Forest | Ramat Hashofet | Ramat Hashofet 3 | Ramat Hashofet KKL Plantings 3 | Most recent year: 2021 | 13 |
| 32.61710000000001,35.11234 | Planted Conifer Forest | Ramat Hashofet | Ramat Hashofet 1 | Ramat Hashofet KKL Plantings 1 | Most recent year: 2021 | 13 |
| 32.65475000000001,34.977940000000004 | Planted Conifer Forest | Kerem Maharal | Kerem Maharal 2 | Kerem Maharal KKL Plantings 2 | Most recent year: 2021 | 9 |
| 32.65475000000001,34.977940000000004 | Planted Conifer Forest | Kerem Maharal | Kerem Maharal Far 2 | Kerem Maharal KKL Plantings 2 | Most recent year: 2021 | 7 |
| 32.66031,34.97883 | Planted Conifer Forest | Kerem Maharal | Kerem Maharal 1 | Kerem Maharal KKL Plantings 1 | Most recent year: 2021 | 7 |
| 32.66031,34.97883 | Planted Conifer Forest | Kerem Maharal | Kerem Maharal Far 1 | Kerem Maharal KKL Plantings 1 | Most recent year: 2021 | 7 |
| 32.661150000000006,34.96866000000001 | Planted Conifer Forest | Kerem Maharal | Kerem Maharal 3 | Kerem Maharal KKL Plantings 3 | Most recent year: 2021 | 11 |
| 32.661150000000006,34.96866000000001 | Planted Conifer Forest | Kerem Maharal | Kerem Maharal Far 3 | Kerem Maharal KKL Plantings 3 | Most recent year: 2021 | 10 |
| 32.663700000000006,35.056180000000005 | Planted Conifer Forest | Elyakim | Elyakim 3 | Elyakim KKL Plantings 3 | Most recent year: 2021 | 6 |
| 32.663700000000006,35.056180000000005 | Planted Conifer Forest | Elyakim | Elyakim Far 3 | Elyakim KKL Plantings 3 | Most recent year: 2021 | 8 |
| 32.66705,35.055690000000006 | Planted Conifer Forest | Elyakim | Elyakim 1 | Elyakim KKL Plantings 1 | Most recent year: 2021 | 6 |
| 32.66705,35.055690000000006 | Planted Conifer Forest | Elyakim | Elyakim Far 1 | Elyakim KKL Plantings 1 | Most recent year: 2021 | 7 |
| 32.667280000000005,35.063010000000006 | Planted Conifer Forest | Elyakim | Elyakim 2 | Elyakim KKL Plantings 2 | Most recent year: 2021 | 6 |
| 32.667280000000005,35.063010000000006 | Planted Conifer Forest | Elyakim | Elyakim Far 2 | Elyakim KKL Plantings 2 | Most recent year: 2021 | 8 |
| 32.98362,35.46043 | Planted Conifer Forest | Meron | Meron 2 | Meron KKL Plantings 2 | Most recent year: 2021 | 15 |
| 32.985780000000005,35.45575 | Planted Conifer Forest | Meron | Meron 1 | Meron KKL Plantings 1 | Most recent year: 2021 | 6 |
| 32.985780000000005,35.45575 | Planted Conifer Forest | Meron | Meron Far 1 | Meron KKL Plantings 1 | Most recent year: 2021 | 7 |
| 32.991890000000005,35.45548000000001 | Planted Conifer Forest | Meron | Meron 3 | Meron KKL Plantings 3 | Most recent year: 2021 | 7 |
| 32.991890000000005,35.45548000000001 | Planted Conifer Forest | Meron | Meron Far 3 | Meron KKL Plantings 3 | Most recent year: 2021 | 5 |
| 33.01091,35.31488 | Planted Conifer Forest | Zuriel | Zuriel 2 | Zuriel KKL Plantings 2 | Most recent year: 2021 | 15 |
| 33.013980000000004,35.317350000000005 | Planted Conifer Forest | Zuriel | Zuriel 3 | Zuriel KKL Plantings 3 | Most recent year: 2021 | 15 |
| 33.01709,35.31004000000001 | Planted Conifer Forest | Zuriel | Zuriel 1 | Zuriel KKL Plantings 1 | Most recent year: 2021 | 5 |
| 33.020250000000004,35.15766000000001 | Planted Conifer Forest | Kabri | Kabri Far 2 | Kabri KKL Plantings 2 | Most recent year: 2021 | 6 |
| 33.02051,35.16411000000001 | Planted Conifer Forest | Kabri | Kabri Far 1 | Kabri KKL Plantings 1 | Most recent year: 2021 | 8 |
| 33.02174000000001,35.17062000000001 | Planted Conifer Forest | Kabri | Kabri 3 | Kabri KKL Plantings 3 | Most recent year: 2021 | 6 |
| 33.02174000000001,35.17062000000001 | Planted Conifer Forest | Kabri | Kabri Far 3 | Kabri KKL Plantings 3 | Most recent year: 2021 | 5 |
| 33.058870000000006,35.23048000000001 | Mediterranean Maquis | Goren | Goren Near 2 new | Goren Near 21 | Most recent year: 2021 | 7 |
| 33.094030000000004,35.56703 | Planted Conifer Forest | Ramot Naftali | Ramot Naftali 2 | Ramot Naftali KKL Plantings 2 | Most recent year: 2021 | 16 |
| 33.09474,35.56141 | Planted Conifer Forest | Ramot Naftali | Ramot Naftali 1 | Ramot Naftali KKL Plantings 1 | Most recent year: 2021 | 12 |
| 33.09852000000001,35.564870000000006 | Planted Conifer Forest | Ramot Naftali | Ramot Naftali 3 | Ramot Naftali KKL Plantings 3 | Most recent year: 2021 | 12 |
| 33.173190000000005,35.55109 | Planted Conifer Forest | Manara | Manara 2 | Manara KKL Plantings 2 | Most recent year: 2021 | 5 |
| 33.173190000000005,35.55109 | Planted Conifer Forest | Manara | Manara Far 2 | Manara KKL Plantings 2 | Most recent year: 2021 | 5 |
| 33.17772000000001,35.54867000000001 | Planted Conifer Forest | Manara | Manara 3 | Manara KKL Plantings 3 | Most recent year: 2021 | 6 |
| 33.17772000000001,35.54867000000001 | Planted Conifer Forest | Manara | Manara Far 3 | Manara KKL Plantings 3 | Most recent year: 2021 | 10 |
| 33.182770000000005,35.548300000000005 | Planted Conifer Forest | Manara | Manara 1 | Manara KKL Plantings 1 | Most recent year: 2021 | 5 |
| 33.182770000000005,35.548300000000005 | Planted Conifer Forest | Manara | Manara Far 1 | Manara KKL Plantings 1 | Most recent year: 2021 | 10 |
