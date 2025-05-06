# ===================================================
# Load necessary libraries
# ===================================================
library(DBI)
library(RPostgres)
library(readr)
library(dplyr)
library(uuid)

# ===================================================
# Connect to PostgreSQL
# ===================================================
con <- dbConnect(
	RPostgres::Postgres(),
	dbname = "Hamaarag_prototype_1",
	host = "localhost",
	port = 5432,
	user = "postgres",
	password = "ronch@hamaarag"
)

# ===================================================
# Load taxonomy backbone CSV
# ===================================================
taxon_df <- read_csv("data/ebird_taxonomy_v2022_shallow.csv")

# ===================================================
# Rename columns for consistency
# ===================================================
taxon_df <- taxon_df %>%
	rename(
		scientific_name = SCIENTIFIC_NAME,
		taxon_order = TAXON_ORDER,
		category = CATEGORY,
		species_code = SPECIES_CODE,
		primary_com_name = PRIMARY_COM_NAME,
		order_name = ORDER,
		family_name = FAMILY,
		hebrew_name = HebName,
		report_as = REPORT_AS
	)

tryCatch({
	
	# ===================================================
	# Insert taxon_entity and taxon_version
	# ===================================================
	species_code_to_taxon_version_id <- list()
	
	for (i in 1:nrow(taxon_df)) {
		
		# Generate UUIDs
		taxon_entity_id <- UUIDgenerate()
		taxon_version_id <- UUIDgenerate()
		
		# Insert into taxon_entity
		dbExecute(con, "
    INSERT INTO taxon_entity (taxon_entity_id, notes)
    VALUES ($1, $2);
  ", params = list(taxon_entity_id,""))
		
		# Insert into taxon_version (initially without report_as)
		dbExecute(con, "
    INSERT INTO taxon_version (
      taxon_version_id, taxon_entity_id, version_year, species_code,
      scientific_name, primary_com_name, hebrew_name, order_name,
      family_name, category, taxon_order
    )
    VALUES ($1, $2, 2022, $3, $4, $5, $6, $7, $8, $9, $10);
  ", params = list(
  	taxon_version_id,
  	taxon_entity_id,
  	taxon_df$species_code[i],
  	taxon_df$scientific_name[i],
  	taxon_df$primary_com_name[i],
  	taxon_df$hebrew_name[i],
  	taxon_df$order_name[i],
  	taxon_df$family_name[i],
  	taxon_df$category[i],
  	taxon_df$taxon_order[i]
  ))
		
		# Save mapping species_code -> taxon_version_id for report_as linking
		species_code_to_taxon_version_id[[taxon_df$species_code[i]]] <- taxon_version_id
	}
	
	# ===================================================
	# Second pass: update report_as UUIDs
	# ===================================================
	for (i in 1:nrow(taxon_df)) {
		if (!is.na(taxon_df$report_as[i]) && taxon_df$report_as[i] != "NA") {
			target_taxon_version_id <- species_code_to_taxon_version_id[[taxon_df$report_as[i]]]
			
			if (!is.null(target_taxon_version_id)) {
				my_taxon_version_id <- species_code_to_taxon_version_id[[taxon_df$species_code[i]]]
				
				dbExecute(con, "
        UPDATE taxon_version
        SET report_as = $1
        WHERE taxon_version_id = $2;
      ", params = list(target_taxon_version_id, my_taxon_version_id))
			}
		}
	}
	cat("Taxonomy backbone loading completed successfully!\n")
	
}, error = function(e) {
	message("An error occurred during insertion: ", e$message)
	
}, finally = {
	# ===================================================
	# Cleanup: delete orphaned taxon_entity records
	# ===================================================
	orphans_removed <- dbExecute(con, "
  DELETE FROM taxon_entity
  WHERE taxon_entity_id NOT IN (
    SELECT DISTINCT taxon_entity_id FROM taxon_version
  );
")
	cat(paste0("Deleted ", orphans_removed, " orphaned taxon_entity records.\n"))
})

# ===================================================
# Disconnect from database
# ===================================================
dbDisconnect(con)
