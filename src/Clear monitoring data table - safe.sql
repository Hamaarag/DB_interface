-- Script to safely clear monitoring data tables for re-loading
-- This script clears all data loaded by load_monitoring_data.py
-- Tables are cleared in dependency order to respect foreign key constraints
-- Includes error handling for missing tables

-- First, rollback any existing aborted transaction
ROLLBACK;

-- Function to safely delete from a table if it exists
DO $$
DECLARE
    table_names text[] := ARRAY[
        'species_observation',
        'species_breeding_relationship', 
        'monitoring_event',
        'monitoring_point',
        'monitoring_site',
        'monitoring_subunit',
        'monitoring_campaign',
        'monitoring_unit'
    ];
    current_table text;
    row_count integer;
BEGIN
    -- Clear tables in dependency order
    FOREACH current_table IN ARRAY table_names
    LOOP
        -- Check if table exists before trying to delete
        IF EXISTS (SELECT 1 FROM information_schema.tables 
                  WHERE table_schema = 'public' 
                  AND table_name = current_table) THEN
            
            EXECUTE format('DELETE FROM %I', current_table);
            GET DIAGNOSTICS row_count = ROW_COUNT;
            RAISE NOTICE 'Cleared % rows from table: %', row_count, current_table;
        ELSE
            RAISE NOTICE 'Table does not exist: %', current_table;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'All monitoring data tables have been successfully cleared';
END
$$;

-- Verify tables are empty (only check tables that exist)
DO $$
DECLARE
    table_names text[] := ARRAY[
        'species_observation',
        'species_breeding_relationship', 
        'monitoring_event',
        'monitoring_point',
        'monitoring_site',
        'monitoring_subunit',
        'monitoring_campaign',
        'monitoring_unit'
    ];
    current_table text;
    row_count integer;
BEGIN
    RAISE NOTICE 'Verification - checking row counts for cleared tables:';
    FOREACH current_table IN ARRAY table_names
    LOOP
        -- Check if table exists and get row count
        IF EXISTS (SELECT 1 FROM information_schema.tables 
                  WHERE table_schema = 'public' 
                  AND table_name = current_table) THEN
            
            EXECUTE format('SELECT COUNT(*) FROM %I', current_table) INTO row_count;
            RAISE NOTICE 'Table %: % rows remaining', current_table, row_count;
        ELSE
            RAISE NOTICE 'Table %: does not exist', current_table;
        END IF;
    END LOOP;
END
$$;

-- Run ANALYZE to update table statistics
ANALYZE;

-- Summary message
SELECT 'Monitoring data tables clearing completed successfully' as status;
