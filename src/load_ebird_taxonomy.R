### Load required libraries ############################################

# This script loads taxonomy data into PostgreSQL from an eBird CSV file.
# It inserts two related structures:
#   (1) taxon_entity (species or species groups)
#   (2) taxon_version (taxonomic snapshot for a specific year)
# It also updates report_as self-references and logs skipped records.

library(DBI)
library(RPostgres)
library(data.table)
library(uuid)

### Configuration ######################################################
version_year <- 2024
mark_as_current <- TRUE  # Set to TRUE if this taxonomy version should be marked as current
taxonomy_filename <- "data/ebird_taxonomy_v2024.csv"

### Connect to PostgreSQL ##############################################
con <- dbConnect(
	Postgres(),
	dbname = "Hamaarag_prototype_1",
	host = "localhost",
	port = 5432,
	user = "postgres",
	password = "ronch@hamaarag"
)

### Load and prepare input CSV #########################################
taxon_df <- fread(taxonomy_filename)
setnames(taxon_df, c("SCIENTIFIC_NAME", "TAXON_ORDER", "CATEGORY", "SPECIES_CODE",
					 "PRIMARY_COM_NAME", "ORDER", "FAMILY", "HebName", "REPORT_AS"),
		 c("scientific_name", "taxon_order", "category", "species_code",
		   "primary_com_name", "order_name", "family_name", "hebrew_name", "report_as"))

### Initialize tracking ################################################
inserted_count <- 0
skipped_taxon_inserts <- data.table()
skipped_report_as <- data.table()

### Insert taxon_entity and taxon_version ##############################
species_code_to_taxon_version_id <- list()

insert_taxon_record <- function(i, taxon_df, con) {
	taxon_entity_id <- UUIDgenerate()
	taxon_version_id <- UUIDgenerate()
	
	tryCatch({
		dbBegin(con)
		
		dbExecute(con, "INSERT INTO taxon_entity (taxon_entity_id, notes) VALUES ($1, $2)",
				  params = list(taxon_entity_id, ""))
		
		dbExecute(con, "INSERT INTO taxon_version (
      taxon_version_id, taxon_entity_id, version_year, species_code,
      scientific_name, primary_com_name, hebrew_name, order_name,
      family_name, category, taxon_order, is_current) VALUES
      ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)",
				  params = list(
				  	taxon_version_id,
				  	taxon_entity_id,
				  	version_year,
				  	taxon_df[i, species_code],
				  	taxon_df[i, scientific_name],
				  	taxon_df[i, primary_com_name],
				  	taxon_df[i, hebrew_name],
				  	taxon_df[i, order_name],
				  	taxon_df[i, family_name],
				  	taxon_df[i, category],
				  	taxon_df[i, taxon_order],
				  	mark_as_current
				  ))
		
		dbCommit(con)
		return(list(success = TRUE, species_code = taxon_df[i, species_code], taxon_version_id = taxon_version_id))
		
	}, error = function(e) {
		dbRollback(con)
		return(list(success = FALSE, skipped_record = data.table(
			species_code = taxon_df[i, species_code],
			reason = e$message
		)))
	})
}

for (i in 1:nrow(taxon_df)) {
	result <- insert_taxon_record(i, taxon_df, con)
	if (result$success) {
		inserted_count <- inserted_count + 1
		species_code_to_taxon_version_id[[result$species_code]] <- result$taxon_version_id
	} else {
		skipped_taxon_inserts <- rbind(skipped_taxon_inserts, result$skipped_record)
	}
}

### Second pass: update report_as UUIDs ###############################

update_report_as <- function(i, taxon_df, uuid_map, con) {
	report_target <- taxon_df[i, report_as]
	
	if (!is.na(report_target) && report_target != "NA" && report_target == "") report_target <- NA
	current_code <- taxon_df[i, species_code]
	
	if (!is.na(report_target) && report_target != "NA") {
		target_uuid <- uuid_map[[report_target]]
		current_uuid <- uuid_map[[current_code]]
		
		if (!is.null(target_uuid) && !is.null(current_uuid) && target_uuid != current_uuid) {
			tryCatch({
				dbBegin(con)
				dbExecute(con, "UPDATE taxon_version SET report_as = $1 WHERE taxon_version_id = $2",
						  params = list(target_uuid, current_uuid))
				dbCommit(con)
				return(NULL)
			}, error = function(e) {
				dbRollback(con)
				return(data.table(
					species_code = current_code,
					report_as = report_target,
					reason = e$message
				))
			})
		} else {
			return(data.table(
				species_code = current_code,
				report_as = report_target,
				reason = "report_as reference not found in taxon_version map"
			))
		}
	} else {
		return(NULL)
	}
}

for (i in 1:nrow(taxon_df)) {
	result <- update_report_as(i, taxon_df, species_code_to_taxon_version_id, con)
	if (!is.null(result)) {
		skipped_report_as <- rbind(skipped_report_as, result)
	}
}

### Cleanup orphaned taxon_entity records #############################
orphans_removed <- dbExecute(con, "DELETE FROM taxon_entity WHERE taxon_entity_id NOT IN (SELECT DISTINCT taxon_entity_id FROM taxon_version)")

### Disconnect and write logs #########################################
dbDisconnect(con)
if (!dir.exists("output")) dir.create("output")

records_attempted <- nrow(taxon_df)

summary_lines <- c(
	paste0("Total records in input CSV: ", records_attempted),
	paste0("- taxon_version records inserted: ", inserted_count),
	paste0("- taxon insert failures: ", nrow(skipped_taxon_inserts)),
	paste0("- orphaned taxon_entity records removed: ", orphans_removed),
	paste0("- report_as values not resolved: ", nrow(skipped_report_as)),
	paste0("- is_current set to: ", mark_as_current)
)

writeLines(summary_lines, "output/taxon_loading_summary.log")

if (nrow(skipped_taxon_inserts) > 0) {
	fwrite(skipped_taxon_inserts, "output/skipped_taxon_inserts.csv")
} else if (file.exists("output/skipped_taxon_inserts.csv")) {
	file.remove("output/skipped_taxon_inserts.csv")
}

if (nrow(skipped_report_as) > 0) {
	fwrite(skipped_report_as, "output/skipped_report_as.csv")
} else if (file.exists("output/skipped_report_as.csv")) {
	file.remove("output/skipped_report_as.csv")
}

cat(paste(summary_lines, collapse = "\n"), "\n")
