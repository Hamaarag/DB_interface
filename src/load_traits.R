# ===================================================
# Load required libraries
# ===================================================
library(DBI)
library(RPostgres)
library(readr)
library(data.table)
library(magrittr)

# ===================================================
# Configuration
# ===================================================
version_year <- 2022

# ===================================================
# Helper Functions
# ===================================================
fetch_enum_values <- function(enum_name) {
	sql <- sprintf("SELECT unnest(enum_range(NULL::%s)) AS val", enum_name)
	dbGetQuery(con, sql)$val
}

get_taxon_version_id <- function(species_code) {
	res <- dbGetQuery(con, "SELECT taxon_version_id FROM taxon_version WHERE species_code = $1 AND version_year = $2", params = list(species_code, version_year))
	if (nrow(res) == 1) res$taxon_version_id else NA
}

mapping_cleanup <- data.table(
	input = c("etsiya.park_forest", "dirt.cliffs", "fish"),
	mapped = c("etsiya park forest", "dirt cliffs", "piscivore")
)

apply_mapping <- function(value_vec) {
	clean_vec <- gsub("[._]", " ", value_vec) %>% trimws() %>% tolower()
	mapped <- mapping_cleanup[match(clean_vec, input), mapped]
	ifelse(!is.na(mapped), mapped, clean_vec)
}

pivot_traits <- function(df, pattern, enum_colname) {
	trait_cols <- grep(pattern, names(df), value = TRUE)
	long_df <- melt(df[, c("SPECIES_CODE", trait_cols), with = FALSE], id.vars = "SPECIES_CODE", variable.name = "trait", value.name = "present")
	long_df <- long_df[present == 1, .(species_code = SPECIES_CODE, trait = gsub(pattern, "", trait))]
	long_df[, (enum_colname) := apply_mapping(trait)][, trait := NULL]
	return(long_df)
}

load_link_table <- function(pivoted_df, table_name, enum_col, enum_type_name) {
	enum_vals <- fetch_enum_values(enum_type_name)
	count <- 0
	for (i in 1:nrow(pivoted_df)) {
		version_id <- get_taxon_version_id(pivoted_df[i, species_code])
		if (is.na(version_id)) {
			counters[table == "skipped_species_traits", count := count + 1]
			next
		}
		val <- pivoted_df[i, get(enum_col)]
		if (!(val %in% enum_vals)) {
			message(sprintf("Skipped unrecognized value '%s' for %s", val, enum_col))
			next
		}
		tryCatch({
			dbExecute(con, paste0("INSERT INTO ", table_name, " (taxon_version_id, ", enum_col, ") VALUES ($1, $2)"),
					  params = list(version_id, val))
			count <- count + 1
		}, error = function(e) {
			message(sprintf("%s insert failed for %s (%s): %s", table_name, pivoted_df[i, species_code], val, e$message))
		})
	}
	link_table_counts <<- rbind(link_table_counts, data.table(table = table_name, count = count))
}

# ===================================================
# Load trait CSV
# ===================================================
csv_data <- fread("data/20231228_BirdSpeciesTraitTable_SingleHeader_shallow.csv")

# ===================================================
# Connect to PostgreSQL
# ===================================================
con <- dbConnect(
	Postgres(),
	dbname = "Hamaarag_prototype_1",
	host = "localhost",
	port = 5432,
	user = "postgres",
	password = "ronch@hamaarag"
)

valid_presence <- fetch_enum_values("presence_enum")

# Initialize counters as data.table
counters <- data.table(
	table = c("species_traits", "presence_IL", "skipped_presence", "skipped_species_traits"),
	count = c(0, 0, 0, 0)
)
link_table_counts <- data.table(table = character(), count = integer())

# ===================================================
# Load species_traits
# ===================================================
for (i in 1:nrow(csv_data)) {
	version_id <- get_taxon_version_id(csv_data[i, SPECIES_CODE])
	if (is.na(version_id)) {
		counters[table == "skipped_species_traits", count := count + 1]
		next
	}
	
	invasiveness <- ifelse(csv_data[i, AlienInvasive] == 1, "alien", ifelse(csv_data[i, NativeInvasive] == 1, "native", NA))
	
	tryCatch({
		dbExecute(con, "
      INSERT INTO species_traits (taxon_version_id, invasiveness, synanthrope, breeding_IL, mass_g, reference)
      VALUES ($1, $2, $3, $4, $5, $6)
    ", params = list(
    	version_id,
    	invasiveness,
    	csv_data[i, Synanthrope],
    	csv_data[i, BreedingIL],
    	csv_data[i, get("Mass..g.")],
    	csv_data[i, Reference]
    ))
		counters[table == "species_traits", count := count + 1]
	}, error = function(e) {
		message(sprintf("species_traits insert failed for %s: %s", csv_data[i, SPECIES_CODE], e$message))
	})
}

# ===================================================
# Load presence_IL (multi-valued)
# ===================================================
for (i in 1:nrow(csv_data)) {
	version_id <- get_taxon_version_id(csv_data[i, SPECIES_CODE])
	if (is.na(version_id)) {
		counters[table == "skipped_species_traits", count := count + 1]
		next
	}
	
	presence_values <- csv_data[i, PresenceIL] %>% strsplit(",") %>% unlist() %>% trimws() %>% tolower()
	
	for (p in presence_values) {
		if (p != "" && !is.na(p) && p %in% valid_presence) {
			tryCatch({
				dbExecute(con, "INSERT INTO presence_il (taxon_version_id, presence_il) VALUES ($1, $2)",
						  params = list(version_id, p))
				counters[table == "presence_IL", count := count + 1]
			}, error = function(e) {
				message(sprintf("presence_IL insert failed for %s (%s): %s", csv_data[i, SPECIES_CODE], p, e$message))
			})
		} else if (!(p %in% valid_presence)) {
			message(sprintf("Skipped unrecognized presence_enum: '%s' for species_code: %s", p, csv_data[i, SPECIES_CODE]))
			counters[table == "skipped_presence", count := count + 1]
		}
	}
}

# ===================================================
# Pivot and load multivalued traits
# ===================================================
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

for (set in trait_sets) {
	pivoted <- pivot_traits(csv_data, set[[1]], set[[3]])
	load_link_table(pivoted, set[[2]], set[[3]], set[[4]])
}

# ===================================================
# Disconnect and report summary to log file
# ===================================================
dbDisconnect(con)

summary_lines <- c(
	"\nSpecies trait loading completed successfully!",
	"Records inserted:",
	paste0("- ", counters$table, ": ", counters$count),
	paste0("- ", link_table_counts$table, ": ", link_table_counts$count)
)

writeLines(summary_lines, "trait_loading_summary.log")
cat(paste(summary_lines, collapse = "\n"), "\n")
