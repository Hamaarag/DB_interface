# ===================================================
# Load necessary libraries
# ===================================================
library(DBI)
library(RPostgres)
library(readr)
library(dplyr)
library(uuid)
library(stringr)

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
# Load CSV data
# ===================================================
csv_data <- read_csv("your_file_path.csv")  # <-- Replace with your real CSV path

# ===================================================
# Rename and prepare columns
# ===================================================
csv_data <- csv_data %>%
	rename(
		scientific_name = SCI_NAME,
		taxon_order = TAXON_ORDER,
		category = CATEGORY,
		species_code = SPECIES_CODE,
		primary_com_name = PRIMARY_COM_NAME,
		order_name = ORDER1,
		family_name = FAMILY,
		hebrew_name = HebName
	)

# ===================================================
# Prepare ENUM mappings (corrected)
# ===================================================

# Presence
presence_mapping <- c(
	"Resident" = "resident",
	"Winter Visitor" = "winter visitor",
	"Summer Visitor" = "summer visitor",
	"Vagrant" = "vagrant",
	"Passage Migrant" = "passage migrant"
)

# Zoogeographic zone
zoogeo_mapping <- list(
	"ZoogeoZone._Mediterranean." = "Mediterranean",
	"ZoogeoZone._Irano.Turanian" = "Irano-Turanian",
	"ZoogeoZone._Sudanese" = "Sudanese",
	"ZoogeoZone._Alpine" = "Alpine",
	"ZoogeoZone._Saharo.Arabian." = "Saharo-Arabian"
)

# Landscape formation
landscape_mapping <- list(
	"LandscapeFormation_wet.Habitat" = "wet habitat",
	"LandscapeFormation_wide.wadis" = "wide wadis",
	"LandscapeFormation_rural.landscape" = "rural landscape",
	"LandscapeFormation_Plains.and.Valleys" = "plains and valleys",
	"LandscapeFormation_Mountainous.area" = "mountainous area",
	"LandscapeFormation_cliffs" = "cliffs",
	"LandscapeFormation_rocks.and.stony.ground" = "rocks and stony ground",
	"LandscapeFormation_Urban.space" = "urban space",
	"LandscapeFormation_Sand.dunes" = "sand dunes"
)

# Vegetation formation
vegetation_mapping <- list(
	"VegetationFormation_reedbed.and.sedges." = "reedbed and sedges",
	"VegetationFormation_gardens.and.parks." = "gardens and parks",
	"VegetationFormation_etsiya.park_forest" = "park forest (Heb: etsiya)",
	"VegetationFormation_forest" = "forest",
	"VegetationFormation_Mediterranean.Maquis" = "Mediterranean maquis",
	"VegetationFormation_low.shrubland." = "low shrubland",
	"VegetationFormation_herbaceous" = "herbaceous",
	"VegetationFormation_high.shrubland" = "high shrubland",
	"VegetationFormation_plantations" = "plantations",
	"VegetationFormation_field.crops." = "field crops"
)

# Vegetation density
density_mapping <- list(
	"VegetationDensity._High" = "high",
	"VegetationDensity._Medium" = "medium",
	"VegetationDensity._Low" = "low"
)

# Nesting ground
nesting_mapping <- list(
	"nest_location_trees" = "trees",
	"nest_location_bushes" = "bushes",
	"nest_location_cliffs" = "cliffs",
	"nest_location_ground" = "ground",
	"nest_location_ruins." = "ruins",
	"nest_location_dirt.cliffs" = "earth cliffs / riverbanks",
	"nest_location_reedbed.and.sedges" = "reedbed and sedges",
	"nest_location_buildings" = "buildings"
)

# Diet type
diet_mapping <- list(
	"DietType._Omnivore" = "omnivore",
	"DietType._Herbivore" = "herbivore",
	"DietType._Fish" = "piscivore",
	"DietType._Invertebrates" = "invertebrates",
	"DietType._Terrestrial.vertebrates" = "terrestrial vertebrates",
	"DietType._Scavenger" = "scavenger"
)

# Foraging ground
foraging_mapping <- list(
	"ForagingGround_Land" = "land",
	"ForagingGround_Trees.and.bushes" = "trees and bushes",
	"ForagingGround_Air" = "air",
	"ForagingGround_Water" = "water"
)

# ===================================================
# Populate conservation_status_lookup
# ===================================================
conservation_world <- csv_data %>%
	select(ConservationCodeWorld, ConservationStatusWorld) %>%
	distinct() %>%
	filter(!is.na(ConservationCodeWorld))

conservation_IL2002 <- csv_data %>%
	select(ConservationCodeIL2002, ConservationStatusIL2002) %>%
	distinct() %>%
	filter(!is.na(ConservationCodeIL2002))

conservation_IL2018 <- csv_data %>%
	select(ConservationCodeIL2018, ConservationStatusIL2018) %>%
	distinct() %>%
	filter(!is.na(ConservationCodeIL2018))

conservation_lookup <- bind_rows(
	conservation_world %>% rename(code = ConservationCodeWorld, status = ConservationStatusWorld),
	conservation_IL2002 %>% rename(code = ConservationCodeIL2002, status = ConservationStatusIL2002),
	conservation_IL2018 %>% rename(code = ConservationCodeIL2018, status = ConservationStatusIL2018)
) %>%
	distinct()

for (i in 1:nrow(conservation_lookup)) {
	tryCatch({
		dbExecute(con, "
      INSERT INTO conservation_status_lookup (code, status)
      VALUES ($1, $2)
      ON CONFLICT (code) DO NOTHING;
    ", params = list(
    	conservation_lookup$code[i],
    	conservation_lookup$status[i]
    ))
	}, error = function(e) {})
}

# ===================================================
# Insert taxon_entity, taxon_version, species_traits, and traits
# ===================================================
species_code_to_taxon_version_id <- list()

for (i in 1:nrow(csv_data)) {
	
	# Generate UUIDs
	taxon_entity_id <- UUIDgenerate()
	taxon_version_id <- UUIDgenerate()
	
	# Map invasiveness
	invasiveness_value <- ifelse(csv_data$AlienInvasive[i] == TRUE, "alien",
								 ifelse(csv_data$NativeInvasive[i] == TRUE, "native", NA))
	
	# Insert into taxon_entity
	dbExecute(con, "
    INSERT INTO taxon_entity (taxon_entity_id, notes)
    VALUES ($1, 'Loaded from CSV');
  ", params = list(taxon_entity_id))
	
	# Insert into taxon_version (initially without report_as)
	dbExecute(con, "
    INSERT INTO taxon_version (
      taxon_version_id, taxon_entity_id, version_year, species_code,
      scientific_name, primary_com_name, hebrew_name, order_name, 
      family_name, category, taxon_order
    )
    VALUES ($1, $2, 2025, $3, $4, $5, $6, $7, $8, $9, $10);
  ", params = list(
  	taxon_version_id,
  	taxon_entity_id,
  	csv_data$species_code[i],
  	csv_data$scientific_name[i],
  	csv_data$primary_com_name[i],
  	csv_data$hebrew_name[i],
  	csv_data$order_name[i],
  	csv_data$family_name[i],
  	csv_data$category[i],
  	csv_data$taxon_order[i]
  ))
	
	# Insert into species_traits
	dbExecute(con, "
    INSERT INTO species_traits (
      taxon_version_id, invasiveness, synanthrope, breeding_IL, mass_g, reference
    )
    VALUES ($1, $2, $3, $4, $5, $6);
  ", params = list(
  	taxon_version_id,
  	invasiveness_value,
  	csv_data$Synanthrope[i],
  	csv_data$BreedingIL[i],
  	csv_data$`Mass..g.`[i],
  	csv_data$Reference[i]
  ))
	
	# Save species_code → taxon_version_id for report_as linking
	species_code_to_taxon_version_id[[csv_data$species_code[i]]] <- taxon_version_id
	
	# ===================================================
	# Insert simple traits (presence_IL)
	# ===================================================
	if (!is.na(csv_data$PresenceIL[i])) {
		presence_clean <- presence_mapping[[csv_data$PresenceIL[i]]]
		if (!is.null(presence_clean)) {
			dbExecute(con, "
        INSERT INTO presence_IL (taxon_version_id, presence_IL)
        VALUES ($1, $2);
      ", params = list(taxon_version_id, presence_clean))
		}
	}
	
	# ===================================================
	# Insert multi-trait link tables
	# ===================================================
	
	## Helper function
	insert_trait <- function(table_name, column_name, value) {
		dbExecute(con, paste0("
      INSERT INTO ", table_name, " (taxon_version_id, ", column_name, ")
      VALUES ($1, $2);
    "), params = list(taxon_version_id, value))
	}
	
	## Zoogeographic zones
	for (field in names(zoogeo_mapping)) {
		if (!is.na(csv_data[[field]][i]) && csv_data[[field]][i] == TRUE) {
			insert_trait("zoogeographic_zone", "zoogeographic_zone", zoogeo_mapping[[field]])
		}
	}
	
	## Landscape formations
	for (field in names(landscape_mapping)) {
		if (!is.na(csv_data[[field]][i]) && csv_data[[field]][i] == TRUE) {
			insert_trait("landscape_formation", "landscape_formation", landscape_mapping[[field]])
		}
	}
	
	## Vegetation formations
	for (field in names(vegetation_mapping)) {
		if (!is.na(csv_data[[field]][i]) && csv_data[[field]][i] == TRUE) {
			insert_trait("vegetation_formation", "vegetation_formation", vegetation_mapping[[field]])
		}
	}
	
	## Vegetation density
	for (field in names(density_mapping)) {
		if (!is.na(csv_data[[field]][i]) && csv_data[[field]][i] == TRUE) {
			insert_trait("vegetation_density", "vegetation_density", density_mapping[[field]])
		}
	}
	
	## Nesting grounds
	for (field in names(nesting_mapping)) {
		if (!is.na(csv_data[[field]][i]) && csv_data[[field]][i] == TRUE) {
			insert_trait("nesting_ground", "nesting_ground", nesting_mapping[[field]])
		}
	}
	
	## Diet types
	for (field in names(diet_mapping)) {
		if (!is.na(csv_data[[field]][i]) && csv_data[[field]][i] == TRUE) {
			insert_trait("diet_type", "diet_type", diet_mapping[[field]])
		}
	}
	
	## Foraging grounds
	for (field in names(foraging_mapping)) {
		if (!is.na(csv_data[[field]][i]) && csv_data[[field]][i] == TRUE) {
			insert_trait("foraging_ground", "foraging_ground", foraging_mapping[[field]])
		}
	}
	
}

# ===================================================
# Second pass: update report_as UUIDs
# ===================================================
for (i in 1:nrow(csv_data)) {
	if (!is.na(csv_data$REPORT_AS[i])) {
		report_as_species_code <- csv_data$REPORT_AS[i]
		target_taxon_version_id <- species_code_to_taxon_version_id[[report_as_species_code]]
		
		if (!is.null(target_taxon_version_id)) {
			my_taxon_version_id <- species_code_to_taxon_version_id[[csv_data$species_code[i]]]
			
			dbExecute(con, "
        UPDATE taxon_version
        SET report_as = $1
        WHERE taxon_version_id = $2;
      ", params = list(target_taxon_version_id, my_taxon_version_id))
		}
	}
}

# ===================================================
# Disconnect
# ===================================================
dbDisconnect(con)

cat("✅ Full data load completed successfully!\n")

