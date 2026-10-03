import dlt

# --- 1. Claims Configuration ---
claims_base_path = "/Volumes/dbr_dev/joshuandegwa_bronze/images/claims"
claims_incoming = f"{claims_base_path}/incoming"
claims_archive = f"{claims_base_path}/archive"

archive_configs = {
    "cloudFiles.cleanSource": "MOVE",
    "cloudFiles.cleanSource.retentionDuration": "1 minute",
    "cloudFiles.cleanSource.moveDestination": claims_archive,
}

# --- 2. Training Images Configuration ---
training_base_path = "/Volumes/dbr_dev/joshuandegwa_bronze/images/training_imgs"
training_schema_loc = f"{training_base_path}/_schemas/training_images_schema"


# --- Table 1: Claim Images (with auto-archive) ---
@dlt.table(
    name="claim_images",
    comment="Raw claim images ingested from Unity Catalog Volume via Auto Loader",
    table_properties={"quality": "bronze"},
)
def claim_images():
  return (
      spark.readStream.format("cloudFiles")
      .option("cloudFiles.format", "binaryFile")
      .options(**archive_configs)
      .load(claims_incoming)
  )


# --- Table 2: Claim Metadata (CSV) ---
@dlt.table(
    name="claim_metadata",
    comment=(
        "Raw claim metadata CSV files ingested from Unity Catalog Volume via"
        " Auto Loader"
    ),
    table_properties={"quality": "bronze"},
)
def claim_metadata():
  return (
      spark.readStream.format("cloudFiles")
      .option("cloudFiles.format", "csv")
      .option("header", "true")
      .option("inferSchema", "true")
      .option(
          "cloudFiles.schemaLocation",
          f"{claims_base_path}/_schemas/claim_metadata_schema",
      )
      .load(f"{claims_base_path}/metadata")
  )


# --- Table 3: Training Images (No archiving) ---
@dlt.table(
    name="training_images",
    comment=(
        "Raw training images ingested from Unity Catalog Volume via Auto"
        " Loader (No archiving)"
    ),
    table_properties={"quality": "bronze"},
)
def training_images():
  return (
      spark.readStream.format("cloudFiles")
      .option("cloudFiles.format", "binaryFile")
      .option("cloudFiles.schemaLocation", training_schema_loc)
      .load(training_base_path)
  )