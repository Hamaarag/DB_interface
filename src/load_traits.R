### Load required libraries ###########################################

# This script loads trait data for species into a PostgreSQL database.
# It performs the following operations:
#   (1) Inserts trait values into the species_traits table
#   (2) Processes and inserts multivalued categorical traits into link tables
#   (3) Logs skipped records and unmatched enum values

library(DBI)
library(RPostgres)
library(data.table)
library(magrittr)

### Configuration ######################################################
version_year <- 2024
trait_data_filename <- "data/BirdSpeciesTraitTable_SingleHeader.csv"

trait_sets <- list(
	list("MigrationType._", "migration_type", "migration_type", "migration_enum"),
	list("ZoogeoZone._", "zoogeographic_zone", "zoogeographic_zone", "zoogeographic_zone_enum"),
	list("LandscapeFormation_", "landscape_formation", "landscape_formation", "landscape_enum"),
	list("VegetationFormation_", "vegetation_formation", "vegetation_formation", "vegetation_formation_enum"),
	list("VegetationDensity._", "vegetation_density", "vegetation_density", "vegetation_density_enum"),
	list("nest_location_", "nesting_ground", "nesting_ground", "nest_enum"),
	list("DietType._", "diet_type", "diet_type", "diet_enum"),
	list("ForagingGround_", "foraging_ground", "foraging_ground", "foraging_ground_enum")
)

conservation_schemes <- list(
	list(column = "ConservationCodeWorld", scheme = "Global"),
	list(column = "ConservationCodeIL2002", scheme = "IL_2002"),
	list(column = "ConservationCodeIL2018", scheme = "IL_2018")
)

### Connect to PostgreSQL ############################################
con <- dbConnect(
	Postgres(),
	dbname = "Hamaarag_prototype_1",
	host = "localhost",
	port = 5432,
	user = "postgres",
	password = "ronch@hamaarag"
)

### Load helper and mapping data #####################################
csv_data <- read.csv(trait_data_filename, fileEncoding = "Windows-1255", stringsAsFactors = FALSE)
csv_data <- as.data.table(csv_data)
csv_data[, PresenceIL := tolower(trimws(PresenceIL))]

trait_value_mapping_df <- fread("data/trait_value_mapping.csv")

# Cache taxon_version_id lookup
version_lookup <- dbGetQuery(con, sprintf("
  SELECT species_code, category, hebrew_name, scientific_name, taxon_version_id
  FROM taxon_version
  WHERE version_year = %d", version_year))

get_taxon_version_id <- function(species_code, category, hebrew_name, scientific_name) {
	row <- version_lookup[
		version_lookup$species_code == species_code &
			version_lookup$category == category &
			(version_lookup$hebrew_name == hebrew_name | version_lookup$scientific_name == scientific_name),
	]
	if (nrow(row) == 1) row$taxon_version_id else NA
}

# Cache enum values for all types
enum_cache <- list(
	presence_enum = dbGetQuery(con, "SELECT unnest(enum_range(NULL::presence_enum)) AS val")$val,
	conservation_status_enum = dbGetQuery(con, "SELECT unnest(enum_range(NULL::conservation_status_enum)) AS val")$val
)

for (set in trait_sets) {
	enum_cache[[set[[4]]]] <- dbGetQuery(con, sprintf("SELECT unnest(enum_range(NULL::%s)) AS val", set[[4]]))$val
}

### Utility functions ##################################################

pivot_traits <- function(df, pattern, enum_colname, mapping_table) {
	trait_cols <- grep(pattern, names(df), value = TRUE)
	long_df <- melt(df[, c("SPECIES_CODE", trait_cols), with = FALSE], id.vars = "SPECIES_CODE", variable.name = "trait", value.name = "present")
	long_df <- long_df[present == 1, .(species_code = SPECIES_CODE, trait = gsub(pattern, "", trait))]
	long_df[, (enum_colname) := apply_mapping(trait, mapping_table)][, trait := NULL]
	return(long_df)
}

apply_mapping <- function(value_vec, mapping_table) {
	clean_vec <- gsub("[._]", " ", value_vec) %>% trimws() %>% tolower()
	mapped <- mapping_table[match(clean_vec, tolower(input)), mapped]
	ifelse(!is.na(mapped), mapped, clean_vec)
}

accumulate_results <- function(results_list) {
	if (length(results_list) == 0) return(data.table())
	rbindlist(results_list, use.names = TRUE, fill = TRUE)
}

### Run main import process ###########################################
counters <- data.table(
	table = c("species_traits", "presence_IL", "skipped_species_traits"),
	count = c(0, 0, 0)
)
skipped_list <- list()
unmatched_list <- list()
link_table_counts <- list()

# insert species_traits records----
for (i in seq_len(nrow(csv_data))) {
	version_id <- get_taxon_version_id(
		csv_data[i, SPECIES_CODE],
		csv_data[i, CATEGORY],
		csv_data[i, HebName],
		csv_data[i, SCIENTIFIC_NAME]
	)
	
	if (is.na(version_id)) {
		skipped_list[[length(skipped_list)+1]] <- data.table(
			species_code = csv_data[i, SPECIES_CODE],
			trait_table = "species_traits",
			trait_value = NA,
			reason = "taxon_version_id not found"
		)
		counters[table == "skipped_species_traits", count := count + 1]
		next
	}
	invasiveness <- ifelse(csv_data[i, AlienInvasive] == 1, "alien", ifelse(csv_data[i, NativeInvasive] == 1, "native", NA))
	tryCatch({
		dbBegin(con)
		dbExecute(con, "INSERT INTO species_traits (taxon_version_id, invasiveness, synanthrope, breeding_IL, mass_g, reference) VALUES ($1, $2, $3, $4, $5, $6)",
				  params = list(
				  	version_id,
				  	invasiveness,
				  	csv_data[i, Synanthrope],
				  	csv_data[i, BreedingIL],
				  	csv_data[i, get("Mass..g.")],
				  	csv_data[i, Reference]
				  ))
		dbCommit(con)
		counters[table == "species_traits", count := count + 1]
	}, error = function(e) {
		dbRollback(con)
		skipped_list[[length(skipped_list)+1]] <- data.table(
			species_code = csv_data[i, SPECIES_CODE],
			trait_table = "species_traits",
			trait_value = invasiveness,
			reason = e$message
		)
		counters[table == "skipped_species_traits", count := count + 1]
	})
}

# insert presence_IL records----
presence_inserted <- 0
for (i in seq_len(nrow(csv_data))) {
	version_id <- get_taxon_version_id(
		csv_data[i, SPECIES_CODE],
		csv_data[i, CATEGORY],
		csv_data[i, HebName],
		csv_data[i, SCIENTIFIC_NAME]
	)
	
	if (is.na(version_id)) next
	presence_values <- strsplit(csv_data[i, PresenceIL], ",")[[1]] %>% trimws() %>% tolower()
	for (p in presence_values) {
		if (p != "" && !is.na(p) && p %in% enum_cache$presence_enum) {
			tryCatch({
				dbBegin(con)
				dbExecute(con, "INSERT INTO presence_il (taxon_version_id, presence_il) VALUES ($1, $2)", params = list(version_id, p))
				dbCommit(con)
				presence_inserted <- presence_inserted + 1
			}, error = function(e) {
				dbRollback(con)
				skipped_list[[length(skipped_list)+1]] <- data.table(
					species_code = csv_data[i, SPECIES_CODE],
					trait_table = "presence_il",
					trait_value = p,
					reason = e$message
				)
			})
		} else if (!(p %in% enum_cache$presence_enum)) {
			unmatched_list[[length(unmatched_list)+1]] <- data.table(
				trait_type = "presence_enum",
				unmatched_value = p,
				species_code = csv_data[i, SPECIES_CODE]
			)
		}
	}
}
counters[table == "presence_IL", count := presence_inserted]

# insert multivalue traits----
for (set in trait_sets) {
	pivoted <- pivot_traits(csv_data, set[[1]], set[[3]], trait_value_mapping_df)
	inserted <- 0
	skipped_local <- list()
	unmatched_local <- list()
	for (i in seq_len(nrow(pivoted))) {
		version_id <- get_taxon_version_id(
			csv_data[i, SPECIES_CODE],
			csv_data[i, CATEGORY],
			csv_data[i, HebName],
			csv_data[i, SCIENTIFIC_NAME]
		)
		
		if (is.na(version_id)) {
			skipped_local[[length(skipped_local)+1]] <- data.table(
				species_code = pivoted[i, species_code],
				trait_table = set[[2]],
				trait_value = pivoted[i, get(set[[3]])],
				reason = "taxon_version_id not found"
			)
			next
		}
		val <- pivoted[i, get(set[[3]])]
		if (!(val %in% enum_cache[[set[[4]]]])) {
			unmatched_local[[length(unmatched_local)+1]] <- data.table(
				trait_type = set[[4]],
				unmatched_value = val,
				species_code = pivoted[i, species_code]
			)
			next
		}
		tryCatch({
			dbBegin(con)
			dbExecute(con, sprintf("INSERT INTO %s (taxon_version_id, %s) VALUES ($1, $2)", set[[2]], set[[3]]),
					  params = list(version_id, val))
			dbCommit(con)
			inserted <- inserted + 1
		}, error = function(e) {
			dbRollback(con)
			skipped_local[[length(skipped_local)+1]] <- data.table(
				species_code = pivoted[i, species_code],
				trait_table = set[[2]],
				trait_value = val,
				reason = e$message
			)
		})
	}
	link_table_counts[[set[[2]]]] <- inserted
	skipped_list <- c(skipped_list, skipped_local)
	unmatched_list <- c(unmatched_list, unmatched_local)
}

# insert conservation status records----
conservation_counts <- data.table(scheme = c("Global", "IL_2002", "IL_2018"), count = 0)
for (i in seq_len(nrow(csv_data))) {
	version_id <- get_taxon_version_id(
		csv_data[i, SPECIES_CODE],
		csv_data[i, CATEGORY],
		csv_data[i, HebName],
		csv_data[i, SCIENTIFIC_NAME]
	)
	
	for (s in conservation_schemes) {
		code <- csv_data[i, get(s$column)]
		if (is.na(version_id)) {
			skipped_list[[length(skipped_list)+1]] <- data.table(
				species_code = csv_data[i, SPECIES_CODE],
				trait_table = "taxon_conservation_status",
				trait_value = code,
				reason = "taxon_version_id not found"
			)
			next
		}
		if (!is.na(code) && code != "" && code %in% enum_cache$conservation_status_enum) {
			tryCatch({
				dbBegin(con)
				dbExecute(con, "INSERT INTO taxon_conservation_status (taxon_version_id, conservation_scheme, conservation_code) VALUES ($1, $2, $3)",
						  params = list(version_id, s$scheme, code))
				dbCommit(con)
				conservation_counts[scheme == s$scheme, count := count + 1]
			}, error = function(e) {
				dbRollback(con)
				skipped_list[[length(skipped_list)+1]] <- data.table(
					species_code = csv_data[i, SPECIES_CODE],
					trait_table = "taxon_conservation_status",
					trait_value = code,
					reason = e$message
				)
			})
		} else if (!(code %in% enum_cache$conservation_status_enum)) {
			unmatched_list[[length(unmatched_list)+1]] <- data.table(
				trait_type = "conservation_status_enum",
				unmatched_value = code,
				species_code = csv_data[i, SPECIES_CODE]
			)
		}
	}
}

skipped_records <- accumulate_results(skipped_list)
unmatched_enum_values <- accumulate_results(unmatched_list)
link_table_counts_dt <- data.table(table = names(link_table_counts), count = unlist(link_table_counts))

### Disconnect and log output #########################################
dbDisconnect(con)
if (!dir.exists("output")) dir.create("output")

records_attempted <- nrow(csv_data)

summary_lines <- c(
	paste0("Total records in input CSV: ", records_attempted),
	paste0("- skipped_species_traits: ", counters[table == "skipped_species_traits", count]),
	"\nSpecies trait loading completed.",
	"Records inserted:",
	paste0("- conservation status: ", paste0(conservation_counts$scheme, ": ", conservation_counts$count, collapse = ", ")),
	paste0("- ", counters[!table %in% c("skipped_species_traits"), table], ": ", counters[!table %in% c("skipped_species_traits"), count]),
	paste0("- ", link_table_counts_dt$table, ": ", link_table_counts_dt$count),
	"",
	paste0("Unmatched ENUM values: ", nrow(unmatched_enum_values))
)

writeLines(summary_lines, "output/trait_loading_summary.log")

if (nrow(skipped_records) > 0) {
	fwrite(skipped_records, "output/skipped_trait_records.csv")
} else if (file.exists("output/skipped_trait_records.csv")) {
	file.remove("output/skipped_trait_records.csv")
	cat("No skipped records. Previous file removed.\n")
} else {
	cat("No skipped records.\n")
}

if (nrow(unmatched_enum_values) > 0) {
	fwrite(unmatched_enum_values, "output/unmatched_enum_values.csv")
} else if (file.exists("output/unmatched_enum_values.csv")) {
	file.remove("output/unmatched_enum_values.csv")
	writeLines("No unmatched ENUM values found. Previous file removed.", "output/unmatched_enum_values.log")
} else {
	writeLines("No unmatched ENUM values found.", "output/unmatched_enum_values.log")
}

cat(paste(summary_lines, collapse = "\n"), "\n")
