# Preliminary test list for data integrity of CSV data files - birds

## Parameter definitions, params are derived from monitoring protocol
**point_n**	The number of plots per factor level (e.g., far/near, shifting/semi-shifting, etc.). This is 3 in the bird monitoring protocol.
**factor_n**	The number of factors per site (e.g., agriculture, dunes, etc.)
**subunit_site_n**	The number of sites per subunit, for maquis and forest units.
**unit_site_n**	The number of sites per unit in each campaign.

1. 
2. In every monitoring year:
	(1) Every factor should have point_n unique points.
	(2) Every site should have factor_n * point_n unique points.
	(3) Every subunit (for maquis and forest units) should have point_n * factor_n * subunit_site_n unique points.
	(4) Every unit should have point_n * factor_n * unit_site_n in every campaign.
   A missing point should have a comment explaining what happened.
3. A point should have:
	(1) one unique set of coordinates
	(2) a single date and start time per campaign. date field should match year, both should match campaign code.
	(3) monitor's name (if missing then should have NA)
	(4) text fields: weather description, disturbances, comments. If missing then NA.
	(5) Site name should match the site that appears in point name
	(6) Factor levels should match whatever appears in the point name
4. Points with zero observations should have a row where scientific name is NA and relevant counts are 0.
5. Boolean field `pilot` should be True / False for campaign T0 (as designated), and False otherwise.
6. There should not be multiple point names for the same set of coordinates (i.e., within a 100m radius)