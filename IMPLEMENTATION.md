# Hamaarag Database Implementation Guide

## Setup Instructions

### Prerequisites

- PostgreSQL 12+
- Python 3.6+
- R 4.4+ with `renv` package
- Required Python packages: pandas>=1.3.0, psycopg2>=2.9.0, python-dotenv>=0.19.0, uuid>=1.30
  
### Database Setup

1. Create a PostgreSQL database:
   ```sql
   CREATE DATABASE hamaarag_db;
   ```

2. Run the schema creation scripts:
   ```bash
   psql -d hamaarag_db -f src/hamaarag_proto_1\ -\ taxonomy\ and\ species\ traits.sql
   psql -d hamaarag_db -f src/monitoring_units_and_observations.sql
   ```

### Configuration

1. Install required Python packages:
   ```bash
   pip install pandas>=1.3.0 psycopg2>=2.9.0 python-dotenv>=0.19.0 uuid>=1.30
   ```

2. Configure database connection by creating a `.env` file in the project root with the following content:
   ```
   DB_NAME=your_database_name
   DB_HOST=your_database_host
   DB_PORT=5432
   DB_USER=your_username
   DB_PASSWORD=your_password
   ```
   
   > **Note**: The `.env` file is excluded from git by `.gitignore` to prevent sensitive credentials from being committed.

2. Enable R environment with `renv`:
   ```R
   renv::restore()
   ```

## Data Loading Process

### Taxonomy Data Loading

Run the taxonomy loading script to import taxonomy data from ebird taxonomy files:

```R
source("src/load_ebird_taxonomy.R")
```

This script:
1. Reads the ebird taxonomy files
2. Generates `taxon_entity` and `taxon_version` records
3. Establishes links between taxonomic versions
4. Records taxonomy changes in `taxon_change_log`

### Species Traits Loading

Run the traits loading script to import species traits:

```R
source("src/load_traits.R")
```

This script:
1. Reads the trait data from CSV files
2. Validates trait values against ENUM types
3. Populates the `species_traits` table and related trait tables
4. Logs any issues to the `output` directory

### Monitoring Data Loading

The monitoring data is loaded from a single source CSV file (`Abreed_and_non_breed.csv`):

```bash
python src/load_monitoring_data.py --config src/config_sample.json
```

This script:
1. Reads database connection details from the `.env` file in the project root
2. Reads the source file containing all monitoring data
3. Extracts and loads monitoring units, sites, and points
4. Extracts and creates campaigns and events
5. Processes species observations from the same file
6. Links observations to taxonomy

## Query Examples

### 1. Get all observations for a specific site:

```sql
SELECT so.*, tv.scientific_name, mp.point_name, ms.site_name, mu.unit_name
FROM species_observation so
JOIN monitoring_event me ON so.event_id = me.event_id
JOIN monitoring_point mp ON me.point_id = mp.point_id
JOIN monitoring_site ms ON mp.site_id = ms.site_id
JOIN monitoring_unit mu ON mp.unit_id = mu.unit_id
JOIN taxon_version tv ON so.taxon_id = tv.taxon_version_id
WHERE ms.site_name = 'Ashalim';
```

### 2. Get breeding species for a specific unit:

```sql
SELECT tv.scientific_name, sbr.is_breeding
FROM species_breeding_relationship sbr
JOIN taxon_version tv ON sbr.taxon_id = tv.taxon_version_id
JOIN monitoring_unit mu ON sbr.unit_id = mu.unit_id
WHERE mu.unit_name = 'Arid South';
```

### 3. Get species counts by habitat type:

```sql
SELECT mp.habitat_type, tv.scientific_name, 
       SUM(so.radius_0_20 + so.radius_20_100 + so.radius_100_250) as total_count
FROM species_observation so
JOIN monitoring_event me ON so.event_id = me.event_id
JOIN monitoring_point mp ON me.point_id = mp.point_id
JOIN taxon_version tv ON so.taxon_id = tv.taxon_version_id
WHERE mp.habitat_type IS NOT NULL
GROUP BY mp.habitat_type, tv.scientific_name
ORDER BY mp.habitat_type, total_count DESC;
```

### 4. Find species observations with first five minutes timing:

```sql
SELECT tv.scientific_name, me.event_date, mu.unit_name, ms.site_name, 
       mp.point_name, so.count_under_250
FROM species_observation so
JOIN monitoring_event me ON so.event_id = me.event_id
JOIN monitoring_point mp ON me.point_id = mp.point_id
JOIN monitoring_site ms ON mp.site_id = ms.site_id
JOIN monitoring_unit mu ON mp.unit_id = mu.unit_id
JOIN taxon_version tv ON so.taxon_id = tv.taxon_version_id
WHERE so.first_five_mins = TRUE
ORDER BY me.event_date DESC;
```

### 5. Get weather statistics for monitoring events:

```sql
SELECT wdl.weather_description, 
       COUNT(me.event_id) as event_count,
       MIN(me.event_date) as first_date,
       MAX(me.event_date) as last_date
FROM monitoring_event me
JOIN weather_description_lookup wdl ON me.weather_code = wdl.weather_code
GROUP BY wdl.weather_description
ORDER BY event_count DESC;
```

## Maintenance Tasks

### Database Backup

```bash
pg_dump -U username -F c -b -v -f hamaarag_backup.dump hamaarag_db
```

### Database Restore

```bash
pg_restore -U username -d hamaarag_db hamaarag_backup.dump
```

### Schema Updates

When updating the schema:

1. Create a backup
2. Update the SQL files
3. Update the DBML files to match
4. Apply changes with migrations (manage carefully to preserve data)
5. Update documentation to reflect changes
