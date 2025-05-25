# Hamaarag Biodiversity Database – Progress Summary (May 2025)

## ✅ Completed Implementation Steps (1–12)

### 1–9: Schema Design and Local Setup
- ✅ **Database Software**: PostgreSQL
- ✅ **Cloud Provider**: Google Cloud SQL
- ✅ **Design Platform**: dbdiagram.io
- ✅ **Schema Design**: Completed for taxonomy, traits, conservation status
  - Normalized to 3NF with use of UUIDs and ENUM constraints
  - Separate `taxon_entity` and `taxon_version` tables support temporal versioning
- ✅ **Database Management Tools**: pgAdmin for local + cloud management
- ✅ **Local Setup**: Local PostgreSQL testing environment created and loaded
- ✅ **Schema Export**: SQL DDL generated from dbdiagram.io
- ✅ **Local Deployment**: Schema deployed and validated locally
- ✅ **Local Testing**: Trait and taxonomy tables successfully populated

### 10–12: Cloud SQL Deployment
- ✅ **Cloud SQL Instance Setup**: PostgreSQL instance created on GCP
- ✅ **Cloud Deployment**: Schema deployed to Google Cloud SQL
- ✅ **Cloud Testing**: All loading scripts tested and validated; view creation successful

---

## 🧬 Core Achievements

- Full bulk loading for `taxon_entity`, `taxon_version`, `species_traits`, and related trait tables using `dbWriteTable()`
- Logging of skipped records and unmatched ENUM values to CSV
- Creation of `taxon_trait_view`: one row per current `taxon_version`, with key fields and traits
- ENUM validation and PostgreSQL constraints maintained
- Query performance improvements via data.table and view flattening

---

## 🔜 Remaining Implementation Steps (13–16)

### 13. Design and Implement Additional Datasets
Planned expansions include:
- 📍 **Species Observations** (event-level)
- 📍 **Abundance and Effort Data**
- 📍 **Monitoring Unit Metadata**
- 📍 **New Traits**:
  - Whether the species breeds in a monitoring unit (taxon × unit)
  - Whether the species interacts with the sampling plot (taxon-specific trait)

### 14. Load Real Data
- ✅ **Completed** for taxonomy and trait tables
- ⏳ Pending for species observations and new trait structures

### 15. Optimize Performance & Indexing
- Will be revisited once observational data and spatial joins are implemented

### 16. Implement API or Query Interface
- To support interaction from R/Python and dashboards (e.g., Shiny apps)

---

## 🌉 Future Strategy – Lakehouse Architecture

In parallel with PostgreSQL development, we plan to implement a **lakehouse-style system** for handling:
- Raw field-collected data (e.g., Fulcrum, Survey123)
- Schema-on-read access to semi-structured observation forms
- Long-term storage of opportunistic and bulk ecological data

The architecture will combine:
- PostgreSQL (curated, validated data)
- Google Cloud Storage or BigQuery (raw event ingestion and archival)
- Automated pipelines for ingestion and transformation

---

