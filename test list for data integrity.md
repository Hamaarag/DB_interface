# Preliminary test list for data integrity of CSV data files - birds

## Parameter definitions, params are derived from monitoring protocol of the given taxon

**point_n**
: The number of plots per factor level (e.g., far/near, shifting/semi-shifting, etc.). This is 3 in the bird monitoring protocol.  
**factor_n**
: The number of factors per site (e.g., agriculture, dunes, etc.)  
**subunit_site_n**
: The number of sites per subunit, for maquis and forest units.  
**unit_site_n**
: The number of sites per unit in each campaign.  

1. In a given monitoring year:
   1. Grouped by unit, subunit, and site, every factor should have `point_n` unique points.  
   2. Grouped by unit and subunit, every site should have `factor_n * point_n` unique points.  
   3. Grouped by unit, every subunit (for maquis and forest units) should have `point_n * factor_n * subunit_site_n` unique points.  
   4. A given unit should have `point_n * factor_n * unit_site_n` unique points.  
   
   A point with no monitoring event for the given year should have a comment explaining what happened in the comments field, and NA in the relevant event metadata fields.  
   
   A point with a monitoring event but with zero observations: see below.

2. A point should have:  
   1. One unique set of coordinates. If there are multiple coordinates for the same point name:  
      - If the coordinates are within 100 m of each other, the coordinates from the most recent monitoring event should be used for all years.  
      - If the coordinates are more than 100 m apart, the point name of the earlier monitoring events should be changed (by appending a suffix '_a', after verifying such a point name does not already exist).  
   2. A single monitoring event per campaign. This means a unique date, start time, monitor's name, weather metadata, etc.  
   3. Monitor's name (if missing, then should have NA).  
   4. Text fields: weather description, disturbances, comments. If missing, then NA.  
   5. Site name should match the site that appears in the point name.  
   6. Factor levels should match whatever appears in the point name.  
   7. Date field should match year; both should match campaign code.
3. Monitoring events with zero observations should have a row where scientific name is NA and relevant counts are 0.
4. Any row with a species name must have a total count >0 (at least one individual observed in one of the distance bands).
5. Boolean field **pilot** should be True / False for campaign T0 (as designated), and False otherwise.
6. There should not be multiple point names for the same set of coordinates (i.e., within a 100m radius). If there are multiple points with the same coordinates, they should all have the most recent point name.