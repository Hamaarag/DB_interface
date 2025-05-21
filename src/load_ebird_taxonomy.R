### Load required libraries ############################################

# This script loads taxonomy data into PostgreSQL from an eBird CSV file.
# It inserts two related structures:
#   (1) taxon_entity (species or species groups)
#   (2) taxon_version (taxonomic snapshot for a specific year)
# It also updates report_as self-references and logs skipped records.
# IMPORTANT: taxon_entity IDs are generated in this script and inserted into
# the database. This script does not check for existing taxonomic entities that
# already exist in the database and may match the taxons in the CSV file.

library(DBI)
library(RPostgres)
library(data.table)
library(uuid)

### Configuration ######################################################
version_year <- 2024
mark_as_current <- TRUE  # Set to TRUE if this taxonomy version should be marked as current
taxonomy_filename <- "data/ebird_taxonomy_v2024.csv"

### Connect to PostgreSQL ##############################################
# for local connection
# con <- dbConnect(
# 	Postgres(),
# 	dbname = "Hamaarag_prototype_1",
# 	host = "localhost",
# 	port = 5432,
# 	user = "postgres",
# 	password = "ronch@hamaarag"
# )

# for remote connection
con <- dbConnect(
	Postgres(),
	dbname = Sys.getenv("DB_NAME"),
	host = Sys.getenv("DB_HOST"),
	port = as.integer(Sys.getenv("DB_PORT")),
	user = Sys.getenv("DB_USER"),
	password = Sys.getenv("DB_PASSWORD")
)

### Load and prepare input CSV #########################################
taxon_df <- fread(taxonomy_filename)
setnames(taxon_df, c("SCIENTIFIC_NAME", "TAXON_ORDER", "CATEGORY", "SPECIES_CODE",
					 "PRIMARY_COM_NAME", "ORDER", "FAMILY", "HebName", "REPORT_AS"),
		 c("scientific_name", "taxon_order", "category", "species_code",
		   "primary_com_name", "order_name", "family_name", "hebrew_name", "report_as"))

### Pre-generate UUIDs #################################################
taxon_df[, taxon_entity_id := replicate(.N, UUIDgenerate())]
taxon_df[, taxon_version_id := replicate(.N, UUIDgenerate())]

### Prepare and load taxon_entity ######################################
taxon_entity_tbl <- unique(taxon_df[, .(taxon_entity_id, notes = "")])
dbWriteTable(con, "taxon_entity", taxon_entity_tbl, append = TRUE, row.names = FALSE)

### Transform report_as species codes to UUIDs (taxon_version_id) and merge ####
# Build species_code → taxon_version_id map
code_map <- taxon_df[, .(species_code, taxon_version_id)]
setnames(code_map, "species_code", "report_as_code")  # for joining

# Left join to get UUIDs for report_as
taxon_df <- merge(
	taxon_df,
	code_map,
	by.x = "report_as",
	by.y = "report_as_code",
	all.x = TRUE
)
setnames(taxon_df, c("taxon_version_id.x", "taxon_version_id.y"),
		 c("taxon_version_id", "report_as_id"))

# log report_as that failed to map as well as succeeded
skipped_report_as <- taxon_df[!is.na(report_as) & is.na(report_as_id), .(
species_code, report_as, reason = "No matching UUID for report_as"
)]
mapped_report_as <- nrow(taxon_df[!is.na(report_as_id)])

# Initialize timer and counters
start_time <- Sys.time()
inserted_count <- nrow(taxon_df)
skipped_taxon_inserts <- data.table()

### Prepare and load taxon_version #####################################
taxon_version_tbl <- taxon_df[, .(
	taxon_version_id,
	taxon_entity_id,
	version_year = version_year,
	species_code,
	scientific_name,
	primary_com_name,
	hebrew_name,
	order_name,
	family_name,
	category,
	taxon_order,
	report_as = report_as_id,  # NEW: now a UUID
	is_current = mark_as_current
)]

dbWriteTable(con, "taxon_version", taxon_version_tbl, append = TRUE, row.names = FALSE)

### Cleanup orphaned taxon_entity records #############################
orphans_removed <- dbExecute(con, "DELETE FROM taxon_entity WHERE taxon_entity_id NOT IN (SELECT DISTINCT taxon_entity_id FROM taxon_version)")

### Disconnect and write logs #########################################
dbDisconnect(con)
if (!dir.exists("output")) dir.create("output")

records_attempted <- nrow(taxon_df)

elapsed_total <- round(difftime(Sys.time(), start_time, units = "mins"), 2)

summary_lines <- c(
	paste0("Total records in input CSV: ", records_attempted),
	paste0("- taxon_version records inserted: ", inserted_count),
	paste0("- taxon insert failures: ", nrow(skipped_taxon_inserts)),
	paste0("- orphaned taxon_entity records removed: ", orphans_removed),
	paste0("- report_as relationships updated: ", mapped_report_as),
	paste0("- report_as values not resolved: ", nrow(skipped_report_as)),
	paste0("- is_current set to: ", mark_as_current),
	paste0("Elapsed time (min): ", elapsed_total)
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
