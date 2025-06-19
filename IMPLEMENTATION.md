# Hamaarag Database Implementation Guide

## Setup Instructions

### Prerequisites

- PostgreSQL 12+
- Python 3.10
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

1. Set up the Python conda environment:
   
   **Option 1**: Run the provided setup script:
   ```bash
   # For Windows cmd.exe
   setup_environment.bat
   
   # For PowerShell
   .\setup_environment.ps1
   ```
   
   **Option 2**: Set up manually:
   ```bash
   # Create conda environment
   conda create --prefix c:\my_python_envs\hamaarag_env python=3.10 -y
   
   # Activate conda environment
   conda activate c:\my_python_envs\hamaarag_env
   
   # Install dependencies
   pip install -r requirements.txt
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

3. Enable R environment with `renv`:
   ```R
   renv::restore()
   ```

## Data Preparation for Loading

Before loading monitoring data into the database, the raw observation data must be cleaned and validated to ensure data quality and prevent constraint violations. This process involves two sequential steps:

### Step 1: Coordinate Cleaning

Raw monitoring data often contains coordinate discrepancies where the same sampling point appears with different GPS coordinates across multiple observation records. This can occur due to GPS measurement errors, device differences, or manual recording variations.

The `clean_coordinates.py` script resolves these discrepancies:

```bash
python src/clean_coordinates.py --input data/raw_observations.csv --output data/observations_cleaned.csv --flagged data/observations_flagged_coordinates.csv --distance-threshold 100
```

**Process:**
- Groups observations by sampling point (unit/subunit/site/point_name)
- Identifies coordinate discrepancies within each point group
- **Auto-corrects** points with coordinates within 100m (configurable) by using the most recent coordinates
- **Flags for manual review** points with larger discrepancies (>100m)
- Outputs cleaned data and a flagged coordinates report for manual curation

**Output files:**
- `*_cleaned.csv`: Cleaned observation data with resolved coordinate discrepancies
- `*_flagged_coordinates.csv`: Report of coordinate conflicts requiring manual review (includes nearest neighbor analysis)

### Step 2: Coordinate Conflict Detection

The database schema enforces a `unique_coordinates` constraint, meaning no two sampling points can share identical coordinates. After coordinate cleaning, different point names might still share the same coordinates, which would cause database loading failures.

The `clean_multiple_point_names_per_location.py` script detects these conflicts:

```bash
python src/clean_multiple_point_names_per_location.py --input data/observations_cleaned.csv --output data/coordinate_conflicts.csv --coordinate-precision 1e-5
```

**Process:**
- Groups cleaned data by coordinates (with configurable precision tolerance)
- Identifies locations where multiple different point names share the same coordinates  
- **Suggests automatic fixes** for conflicts within the same unit/site (keeps most recent point name)
- **Flags for manual review** conflicts across different units/sites
- Outputs a detailed conflict report

**Output file:**
- `*_coordinate_conflicts.csv`: Report of coordinate conflicts with suggested resolutions

**Conflict report includes:**
- `coordinates`: The shared coordinate pair
- `conflict_count`: Number of different points at this location
- `units`, `sites`, `point_names`: Details of conflicting points
- `years`: Years when each point was observed
- `suggested_fix`: Recommended resolution (automatic or manual review)

### Step 3: Manual Data Curation

Before proceeding to database loading:

1. **Review flagged coordinates** (`*_flagged_coordinates.csv`) and resolve large coordinate discrepancies
2. **Review coordinate conflicts** (`*_coordinate_conflicts.csv`) and implement suggested fixes or manual resolutions
3. **Update source data** or create coordinate override files as needed
4. **Re-run both cleaning scripts** until no conflicts remain

**Important:** Database loading will fail if coordinate conflicts remain unresolved due to the `unique_coordinates` constraint.

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
python src/load_monitoring_data.py --config src/config.json
```

The config.json file supports the following parameters:
- `files.source_file`: Path to the CSV file containing monitoring data
- `mappings`: Transformation mappings for various field values
- `taxon_version.version_year`: (Optional) Year of the taxonomy version to use for species mapping

Example config.json:
```json
{
  "files": {
    "source_file": "./data/Abreed_and_non_breed.csv"
  },
  "mappings": {
    "species_codes": {
      "source_column": "species_code",
      "target_table": "taxon_version",
      "target_column": "species_code",
      "filter": {
        "is_current": true
      }
    },
    "breeding_status": {
      "breeding": true,
      "non-breeding": false
    },
    "interaction": {
      "yes": true,
      "no": false
    }
  },
  "taxon_version": {
    "version_year": 2023
  }
}
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
