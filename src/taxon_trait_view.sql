CREATE OR REPLACE VIEW taxon_trait_view AS
SELECT
  tv.version_year,
  tv.species_code,
  tv.scientific_name,
  tv.hebrew_name,
  tv.category,
  -- Show species code instead of UUID for report_as
  ra.species_code AS report_as,

  st.invasiveness,
  st.synanthrope,
  st.breeding_il,

  string_agg(DISTINCT p.presence_il::text, ', ')               AS presence_il,
  string_agg(DISTINCT mt.migration_type::text, ', ')           AS migration_type,
  string_agg(DISTINCT zz.zoogeographic_zone::text, ', ')       AS zoogeographic_zone,
  string_agg(DISTINCT lf.landscape_formation::text, ', ')      AS landscape_formation,
  string_agg(DISTINCT vf.vegetation_formation::text, ', ')     AS vegetation_formation,
  string_agg(DISTINCT vd.vegetation_density::text, ', ')       AS vegetation_density,
  string_agg(DISTINCT ng.nesting_ground::text, ', ')           AS nesting_ground,
  string_agg(DISTINCT dt.diet_type::text, ', ')                AS diet_type,
  string_agg(DISTINCT fg.foraging_ground::text, ', ')          AS foraging_ground,

  gc.conservation_code        AS conservation_global,
  gcl.status_description      AS conservation_global_description,
  ic.conservation_code        AS conservation_IL2018,
  icl.status_description      AS conservation_IL2018_description

FROM taxon_version tv

-- Join to get the species code for report_as UUID
LEFT JOIN taxon_version ra ON ra.taxon_version_id = tv.report_as

LEFT JOIN species_traits st ON st.taxon_version_id = tv.taxon_version_id
LEFT JOIN presence_il p ON p.taxon_version_id = tv.taxon_version_id
LEFT JOIN migration_type mt ON mt.taxon_version_id = tv.taxon_version_id
LEFT JOIN zoogeographic_zone zz ON zz.taxon_version_id = tv.taxon_version_id
LEFT JOIN landscape_formation lf ON lf.taxon_version_id = tv.taxon_version_id
LEFT JOIN vegetation_formation vf ON vf.taxon_version_id = tv.taxon_version_id
LEFT JOIN vegetation_density vd ON vd.taxon_version_id = tv.taxon_version_id
LEFT JOIN nesting_ground ng ON ng.taxon_version_id = tv.taxon_version_id
LEFT JOIN diet_type dt ON dt.taxon_version_id = tv.taxon_version_id
LEFT JOIN foraging_ground fg ON fg.taxon_version_id = tv.taxon_version_id

LEFT JOIN taxon_conservation_status gc
  ON gc.taxon_version_id = tv.taxon_version_id AND gc.conservation_scheme = 'Global'
LEFT JOIN conservation_status_lookup gcl
  ON gcl.status_code = gc.conservation_code

LEFT JOIN taxon_conservation_status ic
  ON ic.taxon_version_id = tv.taxon_version_id AND ic.conservation_scheme = 'IL_2018'
LEFT JOIN conservation_status_lookup icl
  ON icl.status_code = ic.conservation_code

WHERE tv.is_current = TRUE
  AND st.taxon_version_id IS NOT NULL

GROUP BY
  tv.version_year,
  tv.species_code,
  tv.scientific_name,
  tv.hebrew_name,
  tv.category,
  ra.species_code,
  st.invasiveness,
  st.synanthrope,
  st.breeding_il,
  gc.conservation_code,
  gcl.status_description,
  ic.conservation_code,
  icl.status_description;
