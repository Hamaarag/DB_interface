-- Script to clear monitoring data tables for re-loading
-- This script clears all data loaded by load_monitoring_data.py
-- Tables are cleared in dependency order to respect foreign key constraints

BEGIN;

-- Step 1: Clear dependent tables first (those with foreign keys)
-- Clear species observations (depends on monitoring_event and taxon_version)
DELETE FROM species_observation;

-- Clear species breeding relationships (depends on monitoring_unit and taxon_version)  
DELETE FROM species_breeding_relationship;

-- Clear monitoring events (depends on monitoring_campaign and monitoring_point)
DELETE FROM monitoring_event;

-- Step 2: Clear monitoring structure tables
-- Clear monitoring points (depends on monitoring_unit and monitoring_site)
DELETE FROM monitoring_point;

-- Clear monitoring sites (depends on monitoring_unit)
DELETE FROM monitoring_site;

-- Clear monitoring campaigns (independent table)
DELETE FROM monitoring_campaign;

-- Clear monitoring units (parent table)
DELETE FROM monitoring_unit;

-- Step 3: Verify tables are empty
SELECT 
    'species_observation' as table_name, 
    COUNT(*) as row_count 
FROM species_observation
UNION ALL
SELECT 
    'species_breeding_relationship' as table_name, 
    COUNT(*) as row_count 
FROM species_breeding_relationship
UNION ALL
SELECT 
    'monitoring_event' as table_name, 
    COUNT(*) as row_count 
FROM monitoring_event
UNION ALL
SELECT 
    'monitoring_point' as table_name, 
    COUNT(*) as row_count 
FROM monitoring_point
UNION ALL
SELECT 
    'monitoring_site' as table_name, 
    COUNT(*) as row_count 
FROM monitoring_site
UNION ALL
SELECT 
    'monitoring_campaign' as table_name, 
    COUNT(*) as row_count 
FROM monitoring_campaign
UNION ALL
SELECT 
    'monitoring_unit' as table_name, 
    COUNT(*) as row_count 
FROM monitoring_unit
ORDER BY table_name;

COMMIT;

-- Optional: Reset any sequences if using serial columns
-- Note: Most tables use UUIDs as primary keys, but some have serial columns
-- Reset the taxon_change_log sequence if it exists and was affected
-- SELECT setval('taxon_change_log_change_id_seq', 1, false);

ANALYZE;

-- Summary message
SELECT 'Monitoring data tables have been successfully cleared and are ready for re-loading' as status;