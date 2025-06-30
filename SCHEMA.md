# Hamaarag Database Schema Reference

## Overview

This document provides a comprehensive reference for the Hamaarag biodiversity database schema. The database consists of two main components:

1. **Taxonomy and Species Traits** - Stores information about species taxonomy, traits, and characteristics
2. **Monitoring Units and Observations** - Stores information about monitoring locations, events, and species observations

## Schema Diagrams

The database schema is available in both SQL and DBML (Database Markup Language) formats:

- SQL schemas:
  - `hamaarag_proto_1 - taxonomy and species traits.sql`
  - `monitoring_units_and_observations.sql`

- DBML schemas:
  - `hamaarag_proto_1 - taxonomy and species traits.dbml`
  - `monitoring_units_and_observations.dbml`
  - `hamaarag_combined_schema.dbml` (combined view of both schemas)

## Core Design Principles

- **Taxonomic Versioning**: The schema enables tracking species through taxonomic changes over time.
- **Trait Modularity**: Species traits are stored in a normalized structure using a core traits table and specialized link tables.
- **Enum Types**: Categorical data is managed using PostgreSQL ENUM types with lookup tables where human-readable descriptions are needed.
- **Monitoring Hierarchy**: The monitoring structure follows a hierarchical organization from units to sites to points.
- **Referential Integrity**: Foreign key constraints ensure data consistency across related tables.

## Taxonomy Module Tables

### taxon_entity

Represents a unique biological taxon that persists across taxonomic revisions.

| Column | Type | Description |
|--------|------|-------------|
| taxon_entity_id | UUID | Primary key, stable identifier across all versions (never changes) |
| notes | TEXT | Optional free-text notes about the entity (e.g., comments on taxonomic decisions) |

### taxon_version

Represents a specific version of a taxon at a point in time.

| Column | Type | Description |
|--------|------|-------------|
| taxon_version_id | UUID | Primary key, unique ID for a specific taxon version |
| taxon_entity_id | UUID | Reference to parent taxon_entity [ON DELETE RESTRICT] (NOT NULL) |
| version_year | INTEGER | Year of this taxonomic version (NOT NULL) |
| species_code | VARCHAR(10) | Code representing the species (typically from an external taxonomy source) (NOT NULL) |
| scientific_name | TEXT | Scientific name (NOT NULL) |
| primary_com_name | TEXT | Primary common name (NOT NULL) |
| hebrew_name | TEXT | Hebrew name (optional) |
| order_name | TEXT | Taxonomic order name |
| family_name | TEXT | Taxonomic family name |
| category | TEXT | Taxonomic category (NOT NULL) |
| taxon_order | INTEGER | Order for display purposes |
| report_as | UUID | ID of a different taxon to report this as [ON DELETE SET NULL] |
| is_current | BOOLEAN | Whether this is the current version (DEFAULT FALSE) |

**Constraints**: UNIQUE (species_code, version_year)

### taxon_change_log

Records changes between taxon versions.

| Column | Type | Description |
|--------|------|-------------|
| change_id | SERIAL | Primary key, unique ID for each change event |
| from_version_id | UUID | Previous version involved in the change [ON DELETE RESTRICT] |
| to_version_id | UUID | New version resulting from the change [ON DELETE RESTRICT] |
| change_type | change_type_enum | Type of change (split, lump, rename, etc.) |
| inherits_relations | BOOLEAN | If true, new version inherits traits/conservation statuses from old version (DEFAULT FALSE) |
| notes | TEXT | Notes explaining the change |

### species_traits

Contains various traits for a taxon version.

| Column | Type | Description |
|--------|------|-------------|
| taxon_version_id | UUID | Primary key, references taxon_version [ON DELETE CASCADE] |
| invasiveness | invasiveness_enum | Whether the species is alien invasive, native invasive (outbreaking) or neither |
| synanthrope | BOOLEAN | Whether the species tends to live in human-modified environments |
| breeding_il | BOOLEAN | Whether the species breeds in Israel |
| associated_with_sampled_habitats | BOOLEAN | Whether species interacts with sampled habitats |
| associated_with_sampled_habitats_comment | TEXT | Comments about habitat association |
| mass_g | FLOAT | Average adult mass in grams |
| reference | TEXT | Literature or source reference for trait data |

### gbif_taxon_link

Links to GBIF taxonomy.

| Column | Type | Description |
|--------|------|-------------|
| taxon_version_id | UUID | Primary key, references taxon_version [ON DELETE CASCADE] |
| gbif_taxon_id | INTEGER | GBIF species ID |
| gbif_version_year | INTEGER | GBIF taxonomy version used |

### conservation_status_lookup

Lookup table for conservation status descriptions. This table provides human-readable descriptions for conservation status codes to avoid storing the description repeatedly in the main conservation status table.

| Column | Type | Description |
|--------|------|-------------|
| conservation_code | conservation_status_enum | Primary key, standardized conservation status code |
| status_description | TEXT | Full description (e.g., Critically Endangered) (NOT NULL, UNIQUE) |

**Pre-populated values**:
- `LC`: Least concern
- `NE`: Not evaluated
- `NT`: Near threatened
- `EN`: Endangered
- `VU`: Vulnerable
- `CR`: Critically endangered
- `DD`: Data deficient
- `RE_AS_BREED`: Regionally extinct as nesting
- `RE`: Regionally extinct
- `EW`: Extinct in the wild
- `EX`: Extinct

### taxon_conservation_status

Links conservation statuses to taxa. The conservation_code field stores only the standardized code (e.g., 'LC') - to get the full description (e.g., 'Least concern'), join with the conservation_status_lookup table on the conservation_code field.

| Column | Type | Description |
|--------|------|-------------|
| taxon_version_id | UUID | References taxon_version [ON DELETE CASCADE] |
| conservation_scheme | TEXT | Scheme name (e.g., Global, IL_2018) (NOT NULL) |
| conservation_code | conservation_status_enum | Code for the status (NOT NULL) |

**Primary Key**: (taxon_version_id, conservation_scheme)

**Note**: No foreign key constraint is used between conservation_code and conservation_status_lookup.conservation_code since the ENUM type already ensures valid values. The lookup table is used purely for normalization to avoid repeating descriptions.

### Trait Link Tables

These tables link taxa to trait values in a many-to-many relationship. Each has a similar structure:

- `migration_type`: Links taxa to migration patterns
- `presence_il`: Records presence types in Israel
- `landscape_formation`: Records landscape preferences
- `vegetation_formation`: Records vegetation type preferences
- `vegetation_density`: Records vegetation density preferences
- `foraging_ground`: Records foraging habitat preferences
- `zoogeographic_zone`: Records zoogeographic zone distributions
- `nesting_ground`: Records nesting habitat preferences
- `diet_type`: Records diet types

Each table has:
- `taxon_version_id` (UUID, FK): References taxon_version [ON DELETE CASCADE]
- A trait field (ENUM type): The specific trait value
- Primary Key on (taxon_version_id, trait_value)

## Monitoring Module Tables

### monitoring_unit

Represents the highest level of organization for monitoring.

| Column | Type | Description |
|--------|------|-------------|
| unit_id | UUID | Primary key |
| unit_name | TEXT | Name of the monitoring unit (NOT NULL) |
| subunit_name | TEXT | Name of a subunit (optional) |
| description | TEXT | Description of the unit |

### monitoring_site

Represents a site within a monitoring unit.

| Column | Type | Description |
|--------|------|-------------|
| site_id | UUID | Primary key |
| unit_id | UUID | Reference to monitoring_unit [ON DELETE RESTRICT] |
| site_name | TEXT | Name of the site (NOT NULL) |
| description | TEXT | Description of the site |

**Constraints**: UNIQUE (unit_id, site_name)

### monitoring_point

Represents a specific point where observations are made.

| Column | Type | Description |
|--------|------|-------------|
| point_id | UUID | Primary key |
| unit_id | UUID | Reference to monitoring_unit [ON DELETE RESTRICT] |
| site_id | UUID | Reference to monitoring_site [ON DELETE RESTRICT] |
| point_name | TEXT | Name of the point (NOT NULL) |
| longitude | NUMERIC(9,6) | Longitude coordinate (NOT NULL) |
| latitude | NUMERIC(8,6) | Latitude coordinate (NOT NULL) |
| habitat_type | habitat_type_enum | Type of habitat ('Basalt', 'Limestone', 'Slope', 'Wadi') |
| agriculture | TEXT | Proximity to agriculture ("Near", "Far", NULL) |
| settlements | TEXT | Proximity to settlements ("Near", "Far", NULL) |
| dunes | dune_type_enum | Dune type ('Shifting', 'Semi-shifting') |
| land_use | land_use_enum | Land use classification ('Bedouin Agriculture', 'KKL Plantings', 'Natural Loess') |
| notes | TEXT | Additional notes |

**Constraints**: 
- UNIQUE (unit_id, point_name)
- UNIQUE (latitude, longitude)

### monitoring_campaign

Represents a monitoring campaign over a period of time.

| Column | Type | Description |
|--------|------|-------------|
| campaign_id | UUID | Primary key |
| campaign_code | TEXT | Unique code for the campaign (NOT NULL, UNIQUE) |
| start_year | INTEGER | Starting year of the campaign (NOT NULL) |
| end_year | INTEGER | Ending year of the campaign (NOT NULL) |
| description | TEXT | Description of the campaign |

**Constraints**: CHECK (start_year <= end_year)

### weather_description_lookup

Lookup table for standardized weather descriptions.

| Column | Type | Description |
|--------|------|-------------|
| weather_code | TEXT | Primary key |
| weather_description | TEXT | Human-readable weather description (NOT NULL) |

**Pre-populated values**:
- `cloudy`: Cloudy
- `clear`: Clear  
- `cool`: Cool
- `cloudy_light.rain`: Cloudy with light rain
- `clear_warm`: Clear and warm
- `part.cloudy`: Partly cloudy
- `cloudy_cool`: Cloudy and cool
- `nice`: Nice
- `light.clouds`: Light clouds
- `clear_light.wind`: Clear with light wind
- `clear_hot`: Clear and hot
- `light.rain`: Light rain
- `nice_no.wind`: Nice without wind

### monitoring_event

Represents a specific monitoring event.

| Column | Type | Description |
|--------|------|-------------|
| event_id | UUID | Primary key |
| campaign_id | UUID | Reference to monitoring_campaign [ON DELETE RESTRICT] |
| point_id | UUID | Reference to monitoring_point [ON DELETE RESTRICT] |
| event_date | DATE | Date of the event (NOT NULL) |
| start_time | TIME | Starting time of the event |
| weather_code | TEXT | Reference to weather_description_lookup |
| temperature | SMALLINT | Temperature rating (ordinal scale from protocol) |
| wind | SMALLINT | Wind rating (ordinal scale from protocol) |
| clouds | SMALLINT | Cloud cover rating (ordinal scale from protocol) |
| precipitation | SMALLINT | Precipitation rating (ordinal scale from protocol) |
| disturbances | TEXT | Description of any disturbances |
| monitors_name | TEXT | Name of the monitor(s) |
| is_pilot | BOOLEAN | Whether this is a pilot study event (default FALSE) |
| notes | TEXT | Additional notes |

**Constraints**: UNIQUE (campaign_id, point_id, event_date)

### species_observation

Represents an observation of a species during a monitoring event.

| Column | Type | Description |
|--------|------|-------------|
| observation_id | UUID | Primary key |
| event_id | UUID | Reference to monitoring_event [ON DELETE RESTRICT] |
| taxon_id | UUID | Reference to taxon_version [ON DELETE RESTRICT] |
| first_five_mins | BOOLEAN | TRUE if observation was in first five minutes, FALSE otherwise, NULL if unknown |
| radius_0_20 | INTEGER | Count within 0-20m radius (DEFAULT 0) |
| radius_20_100 | INTEGER | Count within 20-100m radius (DEFAULT 0) |
| radius_100_250 | INTEGER | Count within 100-250m radius (DEFAULT 0) |
| radius_over_250 | INTEGER | Count beyond 250m radius (DEFAULT 0) |
| count_under_250 | INTEGER | Generated column (GENERATED ALWAYS AS radius_0_20 + radius_20_100 + radius_100_250 STORED) |
| is_interacting | BOOLEAN | Whether species was interacting with the sampling point |
| notes | TEXT | Additional notes |

**Constraints**: CHECK (radius_0_20 >= 0 AND radius_20_100 >= 0 AND radius_100_250 >= 0 AND radius_over_250 >= 0)

### species_breeding_relationship

Documents breeding status of species at monitoring units.

| Column | Type | Description |
|--------|------|-------------|
| relationship_id | UUID | Primary key |
| unit_id | UUID | Reference to monitoring_unit [ON DELETE RESTRICT] |
| taxon_id | UUID | Reference to taxon_version [ON DELETE RESTRICT] |
| is_breeding | BOOLEAN | Whether the species breeds in this unit (NOT NULL) |
| notes | TEXT | Additional notes |

**Constraints**: UNIQUE (unit_id, taxon_id)

## ENUM Types

The database uses PostgreSQL ENUM types to enforce valid values for categorical fields:

### conservation_status_enum
- `LC`: Least concern
- `NE`: Not evaluated
- `NT`: Near threatened
- `EN`: Endangered
- `VU`: Vulnerable
- `CR`: Critically endangered
- `DD`: Data deficient
- `RE_AS_BREED`: Regionally extinct as nesting
- `RE`: Regionally extinct
- `EW`: Extinct in the wild
- `EX`: Extinct

### migration_enum
- `resident`
- `long-range migrant`
- `short-range migrant`
- `nomadic`

### presence_enum
- `vagrant`
- `winter visitor`
- `summer visitor`
- `resident`
- `passage migrant`

### landscape_enum
- `wet habitat`
- `wide wadis`
- `rural landscape`
- `plains and valleys`
- `mountainous area`
- `cliffs`
- `rocks and stony ground`
- `urban space`
- `sand dunes`

### vegetation_formation_enum
- `reedbed and sedges`
- `gardens and parks`
- `etsiya park forest`
- `forest`
- `Mediterranean maquis`
- `low shrubland`
- `herbaceous`
- `high shrubland`
- `plantations`
- `field crops`

### vegetation_density_enum
- `high`
- `medium`
- `low`

### nest_enum
- `trees`
- `bushes`
- `cliffs`
- `ground`
- `ruins`
- `dirt cliffs`
- `reedbed and sedges`
- `buildings`

### diet_enum
- `omnivore`
- `herbivore`
- `piscivore`
- `invertebrates`
- `terrestrial vertebrates`
- `scavenger`

### foraging_ground_enum
- `land`
- `trees and bushes`
- `air`
- `water`

### zoogeographic_zone_enum
- `Mediterranean`
- `Irano-Turanian`
- `Sudanese`
- `Alpine`
- `Saharo-Arabian`

### change_type_enum
- `split`
- `lump`
- `rename`
- `new`
- `deprecated`

### invasiveness_enum
- `alien`
- `native`

### habitat_type_enum
- `Basalt`
- `Limestone`
- `Slope`
- `Wadi`

### dune_type_enum
- `Shifting`
- `Semi-shifting`

### land_use_enum
- `Bedouin Agriculture`
- `KKL Plantings`
- `Natural Loess`

## Cross-Schema Relationships

The taxonomy and monitoring modules are connected through:

1. **species_observation.taxon_id** references **taxon_version.taxon_version_id**
2. **species_breeding_relationship.taxon_id** references **taxon_version.taxon_version_id**

These connections enable tracking species observations over time and linking them to the appropriate taxonomic version.
