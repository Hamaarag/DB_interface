-- Enum types for categorical data
CREATE TYPE dune_type_enum AS ENUM (
  'Shifting',
  'Semi-shifting'
);

CREATE TYPE habitat_type_enum AS ENUM (
  'Basalt',
  'Limestone',
  'Slope',
  'Wadi'
);

CREATE TYPE land_use_enum AS ENUM (
  'Bedouin Agriculture',
  'KKL Plantings',
  'Natural Loess'
);

-- Lookup table for weather descriptions
CREATE TABLE weather_description_lookup (
  weather_code TEXT PRIMARY KEY,
  weather_description TEXT NOT NULL
);

-- Insert standard weather descriptions
INSERT INTO weather_description_lookup (weather_code, weather_description) VALUES
  ('cloudy', 'Cloudy'),
  ('clear', 'Clear'),
  ('cool', 'Cool'),
  ('cloudy_light.rain', 'Cloudy with light rain'),
  ('clear_warm', 'Clear and warm'),
  ('part.cloudy', 'Partly cloudy'),
  ('cloudy_cool', 'Cloudy and cool'),
  ('nice', 'Nice'),
  ('light.clouds', 'Light clouds'),
  ('clear_light.wind', 'Clear with light wind'),
  ('clear_hot', 'Clear and hot'),
  ('light.rain', 'Light rain'),
  ('nice_no.wind', 'Nice without wind'),
  ('windy.rain_bursts', 'Windy with rain bursts');

-- Monitoring Unit Table
CREATE TABLE monitoring_unit (
  unit_id UUID PRIMARY KEY,
  unit_name TEXT NOT NULL UNIQUE,
  description TEXT
);

-- Monitoring Subunit Table
CREATE TABLE monitoring_subunit (
  subunit_id UUID PRIMARY KEY,
  unit_id UUID REFERENCES monitoring_unit(unit_id) ON DELETE RESTRICT,
  subunit_name TEXT NOT NULL,
  description TEXT,
  
  CONSTRAINT unique_subunit_in_unit UNIQUE (unit_id, subunit_name)
);

-- Monitoring Site Table
CREATE TABLE monitoring_site (
  site_id UUID PRIMARY KEY,
  unit_id UUID REFERENCES monitoring_unit(unit_id) ON DELETE RESTRICT,
  subunit_id UUID REFERENCES monitoring_subunit(subunit_id) ON DELETE RESTRICT,
  site_name TEXT NOT NULL,
  description TEXT,
  
  -- Site names must be unique within their container
  -- For sites with subunits: unique within subunit
  -- For sites without subunits: unique within unit
  CONSTRAINT unique_site_in_subunit UNIQUE (subunit_id, site_name),
  CONSTRAINT unique_site_in_unit_only UNIQUE (unit_id, site_name) DEFERRABLE INITIALLY DEFERRED
);

-- Monitoring Point Table
CREATE TABLE monitoring_point (
  point_id UUID PRIMARY KEY,
  site_id UUID REFERENCES monitoring_site(site_id) ON DELETE RESTRICT,
  point_name TEXT NOT NULL,
  longitude NUMERIC(9,6) NOT NULL,
  latitude NUMERIC(8,6) NOT NULL,
  habitat_type habitat_type_enum,
  agriculture TEXT, -- Categorical field (e.g., "Near", "Far", NULL)
  settlements TEXT, -- Categorical field (e.g., "Near", "Far", NULL)
  dunes dune_type_enum,
  land_use land_use_enum,
  notes TEXT,
  
  CONSTRAINT unique_point_in_site UNIQUE (site_id, point_name),
  CONSTRAINT unique_coordinates UNIQUE (latitude, longitude)
);

-- Monitoring Campaign Table
CREATE TABLE monitoring_campaign (
  campaign_id UUID PRIMARY KEY,
  campaign_code TEXT NOT NULL UNIQUE,
  start_year INTEGER NOT NULL,
  end_year INTEGER NOT NULL,
  description TEXT,
  
  CONSTRAINT valid_years CHECK (start_year <= end_year)
);

-- Monitoring Event Table
CREATE TABLE monitoring_event (
  event_id UUID PRIMARY KEY,
  campaign_id UUID REFERENCES monitoring_campaign(campaign_id) ON DELETE RESTRICT,
  point_id UUID REFERENCES monitoring_point(point_id) ON DELETE RESTRICT,
  event_date DATE NOT NULL,
  start_time TIME,
  weather_code TEXT REFERENCES weather_description_lookup(weather_code),
  temperature SMALLINT, -- Using ordinal scale from protocol
  wind SMALLINT,        -- Using ordinal scale from protocol
  clouds SMALLINT,      -- Using ordinal scale from protocol
  precipitation SMALLINT, -- Using ordinal scale from protocol
  disturbances TEXT,
  monitors_name TEXT,
  is_pilot BOOLEAN DEFAULT FALSE, -- Whether this is a pilot study event
  notes TEXT,
  
  CONSTRAINT unique_event UNIQUE (campaign_id, point_id, event_date)
);

-- Species Observation Table
CREATE TABLE species_observation (
  observation_id UUID PRIMARY KEY,
  event_id UUID REFERENCES monitoring_event(event_id) ON DELETE RESTRICT,
  taxon_id UUID REFERENCES taxon_version(taxon_version_id) ON DELETE RESTRICT,
  first_five_mins BOOLEAN, -- TRUE if observation was in first five minutes (formerly 'A'), FALSE otherwise (formerly 'B'), NULL if unknown
  radius_0_20 INTEGER DEFAULT 0,     -- Count within 0-20m radius
  radius_20_100 INTEGER DEFAULT 0,   -- Count within 20-100m radius
  radius_100_250 INTEGER DEFAULT 0,  -- Count within 100-250m radius
  radius_over_250 INTEGER DEFAULT 0, -- Count beyond 250m radius
  count_under_250 INTEGER GENERATED ALWAYS AS 
    (radius_0_20 + radius_20_100 + radius_100_250) STORED NOT NULL,
  is_interacting BOOLEAN,           -- Whether bird was interacting with the sampling point (TRUE) or just flying over (FALSE)
  notes TEXT,
  
  CONSTRAINT valid_radius_values CHECK (
    radius_0_20 >= 0 AND 
    radius_20_100 >= 0 AND 
    radius_100_250 >= 0 AND 
    radius_over_250 >= 0
  )
);

-- Species Breeding Relationship Table
CREATE TABLE species_breeding_relationship (
  relationship_id UUID PRIMARY KEY,
  unit_id UUID REFERENCES monitoring_unit(unit_id) ON DELETE RESTRICT,
  taxon_id UUID REFERENCES taxon_version(taxon_version_id) ON DELETE RESTRICT,
  is_breeding BOOLEAN NOT NULL,
  notes TEXT,
  
  CONSTRAINT unique_breeding_relationship UNIQUE (unit_id, taxon_id)
);
