# Hamaarag Database Glossary (Version: Updated to May 2025)

## Tables

### 1. `taxon_entity`
- `taxon_entity_id` (UUID, PK): Stable identifier for a taxonomic unit across all versions (never changes).
- `notes` (TEXT): Optional free-text notes about the entity (e.g., comments on taxonomic decisions).

### 2. `taxon_version`
- `taxon_version_id` (UUID, PK): Unique ID for a specific taxon version (one version per year or update).
- `taxon_entity_id` (UUID, FK): Links the version to the stable entity ID. `[ON DELETE RESTRICT]`
- `version_year` (INTEGER, NOT NULL): Year of this version definition.
- `species_code` (VARCHAR(10), NOT NULL): Code representing the species (typically from an external taxonomy source).
- `scientific_name` (TEXT, NOT NULL): Scientific name of the species.
- `primary_com_name` (TEXT, NOT NULL): Primary common name (likely in English).
- `hebrew_name` (TEXT): Common name in Hebrew.
- `order_name` (TEXT): Taxonomic order name (e.g., Passeriformes).
- `family_name` (TEXT): Taxonomic family name (e.g., Corvidae).
- `category` (TEXT, NOT NULL): Group classification (e.g., Birds, Mammals).
- `taxon_order` (INTEGER): Custom sort order for species (e.g., for displaying checklists).
- `report_as` (UUID, FK): Optional pointer to another taxon version that this one should be reported as. `[ON DELETE SET NULL]`
- `is_current` (BOOLEAN, default FALSE): Marks whether this is the current valid version.
- `UNIQUE (species_code, version_year)`

### 3. `taxon_change_log`
- `change_id` (SERIAL, PK): Unique ID for each change event.
- `from_version_id` (UUID, FK): Previous version involved in the change. `[ON DELETE RESTRICT]`
- `to_version_id` (UUID, FK): New version resulting from the change. `[ON DELETE RESTRICT]`
- `change_type` (`change_type_enum`): Type of change (split, lump, rename, etc.).
- `inherits_relations` (BOOLEAN): If true, new version inherits traits/conservation statuses from old version.
- `notes` (TEXT): Notes explaining the change.

### 4. `species_traits`
- `taxon_version_id` (UUID, PK/FK): Links traits to a specific taxon version. `[ON DELETE CASCADE]`
- `invasiveness` (`invasiveness_enum`): Whether the species is alien or native.
- `synanthrope` (BOOLEAN): Whether the species tends to live in human-modified environments.
- `breeding_IL` (BOOLEAN): Indicates whether the species breeds in Israel.
- `mass_g` (FLOAT): Average adult mass in grams.
- `reference` (TEXT): Literature or source reference for trait data.

### 5. `gbif_taxon_link`
- `taxon_version_id` (UUID, PK/FK): Links to GBIF ID for a given taxon version. `[ON DELETE CASCADE]`
- `gbif_taxon_id` (INTEGER, nullable): GBIF species ID.
- `gbif_version_year` (INTEGER, nullable): GBIF taxonomy version used.

### 6. `conservation_status_lookup`
- `status_code` (`conservation_status_enum`, PK): Standardized conservation status code.
- `status_description` (TEXT, UNIQUE): Full description (e.g., Critically Endangered).

### 7. `taxon_conservation_status`
- `taxon_version_id` (UUID, FK): Links conservation status to a taxon version. `[ON DELETE CASCADE]`
- `conservation_scheme` (TEXT, NOT NULL): Scheme name (e.g., Global, IL_2018).
- `conservation_code` (`conservation_status_enum`, NOT NULL): Code for the status.
- `PRIMARY KEY (taxon_version_id, conservation_scheme)`

### 8–15. Trait Link Tables
- One table each: `migration_type`, `presence_il`, `landscape_formation`, `vegetation_formation`, `vegetation_density`, `foraging_ground`, `zoogeographic_zone`, `nesting_ground`, `diet_type`
- Fields:
  - `taxon_version_id` (UUID, FK): Links trait to a specific taxon version. `[ON DELETE CASCADE]`
  - (trait field) (`ENUM`): Specific trait assigned (e.g., `migration_type = 'resident'`)
  - `PRIMARY KEY (taxon_version_id, trait_value)`

---

## ENUM Types

- **`conservation_status_enum`**: LC, NE, NT, EN, VU, CR, DD, RE_AS_BREED, RE, EW, EX
- **`migration_enum`**: resident, long-range migrant, short-range migrant, nomadic
- **`presence_enum`**: vagrant, winter visitor, summer visitor, resident, passage migrant
- **`landscape_enum`**: wet habitat, wide wadis, rural landscape, plains and valleys, etc.
- **`vegetation_formation_enum`**: reedbed, forest types, gardens, etc.
- **`vegetation_density_enum`**: high, medium, low
- **`nest_enum`**: trees, bushes, cliffs, ground, ruins, etc.
- **`diet_enum`**: omnivore, herbivore, invertebrates, piscivore, etc.
- **`foraging_ground_enum`**: land, trees and bushes, air, water
- **`zoogeographic_zone_enum`**: Mediterranean, Irano-Turanian, Sudanese, Alpine, Saharo-Arabian
- **`change_type_enum`**: split, lump, rename, new, deprecated
- **`invasiveness_enum`**: alien, native
