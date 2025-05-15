-- Seed values for conservation_status_lookup

INSERT INTO conservation_status_lookup (status_code, status_description) VALUES
  ('LC', 'Least concern'),
  ('NE', 'Not evaluated'),
  ('NT', 'Near threatened'),
  ('EN', 'Endangered'),
  ('VU', 'Vulnerable'),
  ('CR', 'Critically endangered'),
  ('DD', 'Data deficient'),
  ('RE_AS_BREED', 'Regionally extinct as nesting'),
  ('RE', 'Regionally extinct'),
  ('EW', 'Extinct in the wild'),
  ('EX', 'Extinct');
