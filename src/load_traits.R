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
trait_data_filename <- "data/20231228_BirdSpeciesTraitTable_SingleHeader.csv"

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
csv_data <- read.csv(trait_data_filename, fileEncoding = "Windows-1255", stringsAsFactors = FALSE) # fread doesn't support this encoding
csv_data <- as.data.table(csv_data)
csv_data[, PresenceIL := tolower(trimws(PresenceIL))]

trait_value_mapping_df <- fread("data/trait_value_mapping.csv")

### Utility functions ##################################################
fetch_enum_values <- function(enum_name, con) {
	sql <- sprintf("SELECT unnest(enum_range(NULL::%s)) AS val", enum_name)
	dbGetQuery(con, sql)$val
}

get_taxon_version_id <- function(species_code, con, version_year) {
	res <- dbGetQuery(con, "SELECT taxon_version_id FROM taxon_version WHERE species_code = $1 AND version_year = $2",
					  params = list(species_code, version_year))
	if (nrow(res) == 1) res$taxon_version_id else NA
}

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

insert_species_trait_record <- function(i, csv_data, con, version_year) {
	version_id <- get_taxon_version_id(csv_data[i, SPECIES_CODE], con, version_year)
	if (is.na(version_id)) {
		return(list(success = FALSE, skipped = data.table(
			species_code = csv_data[i, SPECIES_CODE],
			trait_table = "species_traits",
			trait_value = NA,
			reason = "taxon_version_id not found"
		)))
	}
	
	invasiveness <- ifelse(csv_data[i, AlienInvasive] == 1, "alien", ifelse(csv_data[i, NativeInvasive] == 1, "native", NA))
	
	tryCatch({
		dbBegin(con)
		dbExecute(con, "INSERT INTO species_traits (taxon_version_id, invasiveness, synanthrope, breeding_IL, mass_g, reference)
                    VALUES ($1, $2, $3, $4, $5, $6)",
				  params = list(
				  	version_id,
				  	invasiveness,
				  	csv_data[i, Synanthrope],
				  	csv_data[i, BreedingIL],
				  	csv_data[i, get("Mass..g.")],
				  	csv_data[i, Reference]
				  ))
		dbCommit(con)
		return(list(success = TRUE))
	}, error = function(e) {
		dbRollback(con)
		return(list(success = FALSE, skipped = data.table(
			species_code = csv_data[i, SPECIES_CODE],
			trait_table = "species_traits",
			trait_value = invasiveness,
			reason = e$message
		)))
	})
}

insert_conservation_status_record <- function(taxon_version_id, scheme, code, valid_codes, species_code) {
	if (is.na(code) || code == "") return(NULL)
	if (!(code %in% valid_codes)) {
		return(list(success = FALSE, skipped = data.table(
			species_code = species_code,
			trait_table = "taxon_conservation_status",
			trait_value = code,
			reason = "Invalid conservation code"
		)))
	}
	tryCatch({
		dbBegin(con)
		dbExecute(con, "INSERT INTO taxon_conservation_status (taxon_version_id, conservation_scheme, conservation_code)
                VALUES ($1, $2, $3)",
				  params = list(taxon_version_id, scheme, code))
		dbCommit(con)
		return(list(success = TRUE))
	}, error = function(e) {
		dbRollback(con)
		return(list(success = FALSE, skipped = data.table(
			species_code = species_code,
			trait_table = "taxon_conservation_status",
			trait_value = code,
			reason = e$message
		)))
	})
}

insert_multivalue_trait <- function(pivoted_df, table_name, enum_col, enum_type_name, con, version_year) {
	enum_vals <- fetch_enum_values(enum_type_name, con)
	inserted <- 0
	skipped <- data.table()
	unmatched <- data.table()
	
	for (i in 1:nrow(pivoted_df)) {
		version_id <- get_taxon_version_id(pivoted_df[i, species_code], con, version_year)
		if (is.na(version_id)) {
			skipped <- rbind(skipped, data.table(
				species_code = pivoted_df[i, species_code],
				trait_table = table_name,
				trait_value = pivoted_df[i, get(enum_col)],
				reason = "taxon_version_id not found"
			))
			next
		}
		
		val <- pivoted_df[i, get(enum_col)]
		if (!(val %in% enum_vals)) {
			unmatched <- rbind(unmatched, data.table(
				trait_type = enum_type_name,
				unmatched_value = val,
				species_code = pivoted_df[i, species_code]
			))
			next
		}
		
		tryCatch({
			dbBegin(con)
			dbExecute(con, sprintf("INSERT INTO %s (taxon_version_id, %s) VALUES ($1, $2)", table_name, enum_col),
					  params = list(version_id, val))
			dbCommit(con)
			inserted <- inserted + 1
		}, error = function(e) {
			dbRollback(con)
			skipped <- rbind(skipped, data.table(
				species_code = pivoted_df[i, species_code],
				trait_table = table_name,
				trait_value = val,
				reason = e$message
			))
		})
	}
	return(list(inserted = inserted, skipped = skipped, unmatched = unmatched))
}

insert_presence_il_record <- function(i, csv_data, con, version_year, valid_presence) {
	skipped <- data.table()
	unmatched <- data.table()
	inserted <- 0
	
	version_id <- get_taxon_version_id(csv_data[i, SPECIES_CODE], con, version_year)
	if (is.na(version_id)) {
		return(list(inserted = 0, skipped = data.table(), unmatched = data.table()))
	}
	
	presence_values <- strsplit(csv_data[i, PresenceIL], ",")[[1]] %>% trimws() %>% tolower()
	for (p in presence_values) {
		if (p != "" && !is.na(p) && p %in% valid_presence) {
			result <- tryCatch({
				dbBegin(con)
				dbExecute(con, "INSERT INTO presence_il (taxon_version_id, presence_il) VALUES ($1, $2)",
						  params = list(version_id, p))
				dbCommit(con)
				list(success = TRUE)
			}, error = function(e) {
				dbRollback(con)
				list(success = FALSE, skipped_record = data.table(
					species_code = csv_data[i, SPECIES_CODE],
					trait_table = "presence_il",
					trait_value = p,
					reason = e$message
				))
			})
			if (!result$success) {
				skipped <- rbind(skipped, result$skipped_record)
			} else {
				inserted <- inserted + 1
			}
		} else if (!(p %in% valid_presence)) {
			unmatched <- rbind(unmatched, data.table(
				trait_type = "presence_enum",
				unmatched_value = p,
				species_code = csv_data[i, SPECIES_CODE]
			))
		}
	}
	return(list(inserted = inserted, skipped = skipped, unmatched = unmatched))
}

### Run main import process ###########################################
counters <- data.table(
	table = c("species_traits", "presence_IL", "skipped_species_traits"),
	count = c(0, 0, 0)
)
link_table_counts <- data.table(table = character(), count = integer())
skipped_records <- data.table()
unmatched_enum_values <- data.table()

# insert species_traits records
for (i in 1:nrow(csv_data)) {
	result <- insert_species_trait_record(i, csv_data, con, version_year)
	if (result$success) {
		counters[table == "species_traits", count := count + 1]
	} else {
		counters[table == "skipped_species_traits", count := count + 1]
		skipped_records <- rbind(skipped_records, result$skipped)
	}
}

# insert presence_IL records
valid_presence <- fetch_enum_values("presence_enum", con)

presence_inserted <- 0
for (i in 1:nrow(csv_data)) {
	result <- insert_presence_il_record(i, csv_data, con, version_year, valid_presence)
	presence_inserted <- presence_inserted + result$inserted
	skipped_records <- rbind(skipped_records, result$skipped)
	unmatched_enum_values <- rbind(unmatched_enum_values, result$unmatched)
}
counters[table == "presence_IL", count := presence_inserted]

# insert multivalue traits
for (set in trait_sets) {
	pivoted <- pivot_traits(csv_data, set[[1]], set[[3]], trait_value_mapping_df)
	result <- insert_multivalue_trait(pivoted, set[[2]], set[[3]], set[[4]], con, version_year)
	link_table_counts <- rbind(link_table_counts, data.table(table = set[[2]], count = result$inserted))
	skipped_records <- rbind(skipped_records, result$skipped)
	unmatched_enum_values <- rbind(unmatched_enum_values, result$unmatched)
}

# insert conservation status records
valid_conservation_codes <- fetch_enum_values("conservation_status_enum", con)
conservation_counts <- data.table(scheme = c("Global", "IL_2002", "IL_2018"), count = 0)

for (i in 1:nrow(csv_data)) {
	version_id <- get_taxon_version_id(csv_data[i, SPECIES_CODE], con, version_year)
	if (is.na(version_id)) {
		for (s in conservation_schemes) {
			code <- csv_data[i, get(s$column)]
			skipped_records <- rbind(skipped_records, data.table(
				species_code = csv_data[i, SPECIES_CODE],
				trait_table = "taxon_conservation_status",
				trait_value = code,
				reason = "taxon_version_id not found"
			))
		}
		next
	}
	for (s in conservation_schemes) {
		code <- csv_data[i, get(s$column)]
		result <- insert_conservation_status_record(version_id, s$scheme, code, valid_conservation_codes, csv_data[i, SPECIES_CODE])
		if (!is.null(result)) {
			if (result$success) {
				conservation_counts[scheme == s$scheme, count := count + 1]
			} else {
				skipped_records <- rbind(skipped_records, result$skipped)
			}
		}
	}
}

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
	paste0("- ", counters[!table %in% c("skipped_species_traits", "skipped_presence"), table], ": ", counters[!table %in% c("skipped_species_traits", "skipped_presence"), count]),
	paste0("- ", link_table_counts$table, ": ", link_table_counts$count),
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
