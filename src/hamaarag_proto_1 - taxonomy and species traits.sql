-- ENUM TYPES CREATION

CREATE TYPE conservation_status_enum AS ENUM (
  'LC',            -- Least concern
  'NE',            -- Not evaluated
  'NT',            -- Near threatened
  'EN',            -- Endangered
  'VU',            -- Vulnerable
  'CR',            -- Critically endangered
  'DD',            -- Data deficient
  'RE_AS_BREED',   -- Regionally extinct as nesting
  'RE',            -- Regionally extinct
  'EW',            -- Extinct in the wild
  'EX'             -- Extinct
);

CREATE TYPE migration_enum AS ENUM (
  'resident',
  'long-range migrant',
  'short-range migrant',
  'nomadic'
);

CREATE TYPE presence_enum AS ENUM (
  'vagrant',
  'winter visitor',
  'summer visitor',
  'resident',
  'passage migrant'
);

CREATE TYPE landscape_enum AS ENUM (
  'wet habitat',
  'wide wadis',
  'rural landscape',
  'plains and valleys',
  'mountainous area',
  'cliffs',
  'rocks and stony ground',
  'urban space',
  'sand dunes'
);

CREATE TYPE vegetation_formation_enum AS ENUM (
  'reedbed and sedges',
  'gardens and parks',
  'etsiya park forest',
  'forest',
  'Mediterranean maquis',
  'low shrubland',
  'herbaceous',
  'high shrubland',
  'plantations',
  'field crops'
);

CREATE TYPE vegetation_density_enum AS ENUM (
  'high',
  'medium',
  'low'
);

CREATE TYPE nest_enum AS ENUM (
  'trees',
  'bushes',
  'cliffs',
  'ground',
  'ruins',
  'dirt cliffs',
  'reedbed and sedges',
  'buildings'
);

CREATE TYPE diet_enum AS ENUM (
  'omnivore',
  'herbivore',
  'piscivore',
  'invertebrates',
  'terrestrial vertebrates',
  'scavenger'
);

CREATE TYPE foraging_ground_enum AS ENUM (
  'land',
  'trees and bushes',
  'air',
  'water'
);

CREATE TYPE zoogeographic_zone_enum AS ENUM (
  'Mediterranean',
  'Irano-Turanian',
  'Sudanese',
  'Alpine',
  'Saharo-Arabian'
);

CREATE TYPE change_type_enum AS ENUM (
  'split',
  'lump',
  'rename',
  'new',
  'deprecated'
);

CREATE TYPE invasiveness_enum AS ENUM (
  'alien',
  'native'
);

-- CORE TAXONOMY STRUCTURE
CREATE TABLE taxon_entity (
  taxon_entity_id UUID PRIMARY KEY,
  notes TEXT
);

CREATE TABLE taxon_version (
  taxon_version_id UUID PRIMARY KEY,
  taxon_entity_id UUID NOT NULL REFERENCES taxon_entity(taxon_entity_id) ON DELETE RESTRICT,
  version_year INTEGER NOT NULL,
  species_code VARCHAR(10) NOT NULL,
  scientific_name TEXT NOT NULL,
  primary_com_name TEXT NOT NULL,
  hebrew_name TEXT,
  order_name TEXT,
  family_name TEXT,
  category TEXT NOT NULL,
  taxon_order INTEGER,
  report_as UUID REFERENCES taxon_version(taxon_version_id) ON DELETE SET NULL,
  is_current BOOLEAN DEFAULT FALSE,
  UNIQUE (species_code, version_year)
);

CREATE TABLE taxon_change_log (
  change_id SERIAL PRIMARY KEY,
  from_version_id UUID REFERENCES taxon_version(taxon_version_id) ON DELETE RESTRICT,
  to_version_id UUID REFERENCES taxon_version(taxon_version_id) ON DELETE RESTRICT,
  change_type change_type_enum,
  inherits_relations BOOLEAN DEFAULT FALSE,
  notes TEXT
);

-- TRAIT TABLES LINKED TO taxon_version_id
CREATE TABLE species_traits (
  taxon_version_id UUID PRIMARY KEY REFERENCES taxon_version(taxon_version_id) ON DELETE CASCADE,
  invasiveness invasiveness_enum,
  synanthrope BOOLEAN,
  breeding_il BOOLEAN,
  mass_g FLOAT,
  reference TEXT
);

CREATE TABLE gbif_taxon_link (
  taxon_version_id UUID PRIMARY KEY REFERENCES taxon_version(taxon_version_id) ON DELETE CASCADE,
  gbif_taxon_id INTEGER,
  gbif_version_year INTEGER
);

CREATE TABLE conservation_status_lookup (
  status_code conservation_status_enum PRIMARY KEY,
  status_description TEXT NOT NULL UNIQUE
);

CREATE TABLE taxon_conservation_status (
  taxon_version_id UUID REFERENCES taxon_version(taxon_version_id) ON DELETE CASCADE,
  conservation_scheme TEXT NOT NULL,
  conservation_code conservation_status_enum NOT NULL,
  PRIMARY KEY (taxon_version_id, conservation_scheme)
);

CREATE TABLE migration_type (
  taxon_version_id UUID REFERENCES taxon_version(taxon_version_id) ON DELETE CASCADE,
  migration_type migration_enum,
  PRIMARY KEY (taxon_version_id, migration_type)
);

CREATE TABLE presence_il (
  taxon_version_id UUID REFERENCES taxon_version(taxon_version_id) ON DELETE CASCADE,
  presence_il presence_enum,
  PRIMARY KEY (taxon_version_id, presence_il)
);

CREATE TABLE landscape_formation (
  taxon_version_id UUID REFERENCES taxon_version(taxon_version_id) ON DELETE CASCADE,
  landscape_formation landscape_enum,
  PRIMARY KEY (taxon_version_id, landscape_formation)
);

CREATE TABLE vegetation_formation (
  taxon_version_id UUID REFERENCES taxon_version(taxon_version_id) ON DELETE CASCADE,
  vegetation_formation vegetation_formation_enum,
  PRIMARY KEY (taxon_version_id, vegetation_formation)
);

CREATE TABLE vegetation_density (
  taxon_version_id UUID REFERENCES taxon_version(taxon_version_id) ON DELETE CASCADE,
  vegetation_density vegetation_density_enum,
  PRIMARY KEY (taxon_version_id, vegetation_density)
);

CREATE TABLE foraging_ground (
  taxon_version_id UUID REFERENCES taxon_version(taxon_version_id) ON DELETE CASCADE,
  foraging_ground foraging_ground_enum,
  PRIMARY KEY (taxon_version_id, foraging_ground)
);

CREATE TABLE zoogeographic_zone (
  taxon_version_id UUID REFERENCES taxon_version(taxon_version_id) ON DELETE CASCADE,
  zoogeographic_zone zoogeographic_zone_enum,
  PRIMARY KEY (taxon_version_id, zoogeographic_zone)
);

CREATE TABLE nesting_ground (
  taxon_version_id UUID REFERENCES taxon_version(taxon_version_id) ON DELETE CASCADE,
  nesting_ground nest_enum,
  PRIMARY KEY (taxon_version_id, nesting_ground)
);

CREATE TABLE diet_type (
  taxon_version_id UUID REFERENCES taxon_version(taxon_version_id) ON DELETE CASCADE,
  diet_type diet_enum,
  PRIMARY KEY (taxon_version_id, diet_type)
);
