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

# Define mapping table for trait values (pattern, table name, column name, enum type)
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

### Utility functions ################################################
apply_mapping <- function(value_vec, mapping_table) {
	clean_vec <- gsub("[._]", " ", value_vec) %>% trimws() %>% tolower()
	mapped <- mapping_table[match(clean_vec, tolower(input)), mapped]
	ifelse(!is.na(mapped), mapped, clean_vec)
}

### Connect to PostgreSQL ############################################
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

### Load helper and mapping data #####################################
trait_data <- read.csv(trait_data_filename, fileEncoding = "UTF-8", stringsAsFactors = FALSE)
trait_data <- as.data.table(trait_data)
trait_data[, PresenceIL := tolower(trimws(PresenceIL))]

trait_value_mapping_df <- fread("data/trait_value_mapping.csv")

# Preload all taxon_version records for the desired year
version_lookup <- dbGetQuery(con, sprintf("
  SELECT species_code, category, hebrew_name, scientific_name, taxon_version_id
  FROM taxon_version
  WHERE version_year = %d", version_year))

setDT(version_lookup)

# Filter version_lookup to only include species with the same Hebrew or
# scientific name as in the trait table
version_lookup_filtered <- version_lookup[
	hebrew_name %in% trait_data$HebName |
		scientific_name %in% trait_data$SCI_NAME]

# Perform join (on species_code + category + either Hebrew or scientific name)
trait_data <- merge(
	trait_data,
	version_lookup_filtered,
	by.y = c("species_code", "category"),
	by.x = c("SPECIES_CODE", "CATEGORY"),
	all.x = TRUE,
	suffixes = c("", "_lookup")
)[HebName == hebrew_name | SCI_NAME == scientific_name]

# Drop temporary columns
trait_data[, c("hebrew_name", "scientific_name") := NULL]

### Cache ENUM values ##################################################
enum_names <- c(
	"presence_enum",
	"conservation_status_enum",
	"migration_enum",
	"zoogeographic_zone_enum",
	"landscape_enum",
	"vegetation_formation_enum",
	"vegetation_density_enum",
	"nest_enum",
	"diet_enum",
	"foraging_ground_enum",
	"invasiveness_enum",
	"change_type_enum"
)

enum_cache <- list()

for (enum_type in enum_names) {
	enum_cache[[enum_type]] <- dbGetQuery(
		con, sprintf("SELECT unnest(enum_range(NULL::%s)) AS val", enum_type)
	)$val
}

for (set in trait_sets) {
	enum_cache[[set[[4]]]] <- dbGetQuery(con, sprintf(
		"SELECT unnest(enum_range(NULL::%s)) AS val", set[[4]])
	)$val
}

### Build species_traits table ########################################
species_traits_tbl <- trait_data[!is.na(taxon_version_id), .(
	taxon_version_id,
	invasiveness = fifelse(AlienInvasive == 1, "alien",
						   fifelse(NativeInvasive == 1, "native", NA_character_)),
	synanthrope = as.logical(Synanthrope),
	breeding_il = as.logical(BreedingIL),
	mass_g = `Mass..g.`,
	reference = Reference
)]

dbWriteTable(con, "species_traits", species_traits_tbl, append = TRUE, row.names = FALSE)

### Build presence_il table ###########################################
presence_il_tbl <- trait_data[!is.na(taxon_version_id), .(
	taxon_version_id,
	presence_il = strsplit(PresenceIL, ",")
)][
	, .(presence_il = unlist(presence_il)), by = taxon_version_id
][presence_il != "" & presence_il %in% enum_cache$presence_enum]

dbWriteTable(con, "presence_il", presence_il_tbl, append = TRUE, row.names = FALSE)

### Build multivalue trait link tables ################################
unmatched_enum_values <- data.table()
for (set in trait_sets) {
	pivoted <- melt(
		trait_data[, c("taxon_version_id", grep(set[[1]], names(trait_data), value = TRUE)), with = FALSE],
		id.vars = "taxon_version_id", variable.name = "trait", value.name = "present"
	)[present == 1, .(
		taxon_version_id,
		value = apply_mapping(gsub(set[[1]], "", trait), trait_value_mapping_df)
	)]
	
	# Filter only valid ENUM values
	valid_enum <- enum_cache[[set[[4]]]]
	unmatched <- pivoted[!value %in% valid_enum]
	
	if (nrow(unmatched) > 0) {
		unmatched[, trait_type := set[[4]]]
		unmatched_enum_values <- rbindlist(list(unmatched_enum_values, unmatched), fill = TRUE)
	}
	
	pivoted <- pivoted[value %in% valid_enum]
	setnames(pivoted, "value", set[[3]])
	
	dbWriteTable(con, set[[2]], pivoted, append = TRUE, row.names = FALSE)
}

### Build and insert conservation statuses ############################
conservation_tbl <- rbindlist(lapply(conservation_schemes,
									 function(scheme) {
									 	trait_data[!is.na(taxon_version_id) & 
									 			   	get(scheme$column) %in% enum_cache$conservation_status_enum,
									 			   .(taxon_version_id,
									 			     conservation_scheme = scheme$scheme,
									 			     conservation_code = get(scheme$column))]
									 }))

dbWriteTable(con, "taxon_conservation_status", conservation_tbl, append = TRUE, row.names = FALSE)

### Write logs ########################################################
if (!dir.exists("output")) dir.create("output")

summary_lines <- c(
	paste0("Trait loading summary – ", Sys.Date()),
	paste0("Total records in raw trait table csv: ", nrow(trait_data)),
	paste0("- species_traits: ", nrow(species_traits_tbl)),
	paste0("- presence_il: ", nrow(presence_il_tbl)),
	paste0("- conservation statuses: ", nrow(conservation_tbl)),
	paste0("- multivalue traits:")
)

for (set in trait_sets) {
	table_name <- set[[2]]
	col_name <- set[[3]]
	count <- tryCatch({
		dbGetQuery(con, sprintf("SELECT COUNT(*) FROM %s", table_name))[[1]]
	}, error = function(e) {
		browser()
		paste0("error counting ", table_name)
	})
	summary_lines <- c(summary_lines, paste0("  • ", table_name, ": ", count))
}

# Write summary log
writeLines(summary_lines, "output/trait_loading_summary.log")
# Write unmatched enum values if any
if (exists("unmatched_enum_values") && nrow(unmatched_enum_values) > 0) {
	# Count how many unmatched per enum type
	enum_summary <- unmatched_enum_values[, .N, by = trait_type]
	
	# Add to summary_lines
	summary_lines <- c(summary_lines, "", "Unmatched ENUM values by type:")
	for (i in seq_len(nrow(enum_summary))) {
		summary_lines <- c(summary_lines, paste0("  • ", enum_summary$trait_type[i], ": ", enum_summary$N[i]))
	}
	
	# Save detailed unmatched values
	fwrite(unmatched_enum_values, "output/unmatched_enum_values.csv")
	message("Unmatched ENUM values written to: output/unmatched_enum_values.csv")
} else {
	writeLines("No unmatched ENUM values found.", "output/unmatched_enum_values.log")
}

cat(paste(summary_lines, collapse = "\n"), "\n")

cat("Trait loading completed.\n")

### Disconnect ########################################################
dbDisconnect(con)