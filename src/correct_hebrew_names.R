library(DBI)
library(RPostgres)
library(data.table)

# Load corrections
corrections <- fread("data/hebrew_name_spelling_correction_table.csv")

# Connect to PostgreSQL
con <- dbConnect(
	Postgres(),
	dbname = "Hamaarag_prototype_1",
	host = "localhost",
	port = 5432,
	user = "postgres",
	password = "ronch@hamaarag"
)

# Apply each correction
for (i in seq_len(nrow(corrections))) {
	old_name <- corrections[i, hebrew_name_ebird]
	new_name <- corrections[i, hebrew_name_hamaarag]
	
	dbExecute(con, "
    UPDATE taxon_version
    SET hebrew_name = $1
    WHERE hebrew_name = $2",
			  params = list(new_name, old_name)
	)
}

# Disconnect
dbDisconnect(con)
