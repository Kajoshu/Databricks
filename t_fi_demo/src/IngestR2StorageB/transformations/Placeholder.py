import dlt

# Derive all paths from the pipeline-resolved catalog and schema
_catalog = spark.conf.get("pipeline.catalog")
_schema  = spark.conf.get("pipeline.schema")
_vol     = f"/Volumes/{_catalog}/{_schema}"

CLAIMS_BASE_PATH     = f"{_vol}/images/claims"
CLAIMS_INCOMING      = f"{CLAIMS_BASE_PATH}/images"
CLAIMS_ARCHIVE       = f"{CLAIMS_BASE_PATH}/archive"
CLAIMS_METADATA_PATH = f"{CLAIMS_BASE_PATH}/metadata"
CLAIMS_SCHEMA_LOC    = f"{CLAIMS_BASE_PATH}/_schemas/claim_metadata_schema"
TRAINING_BASE_PATH   = f"{_vol}/images/training_imgs"
TRAINING_SCHEMA_LOC  = f"{_vol}/images/training_imgs/_schemas/training_images_schema"

archive_configs = {
    "cloudFiles.cleanSource": "archive",
    "cloudFiles.archive.dir": CLAIMS_ARCHIVE,
}


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
      .load(CLAIMS_INCOMING)
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
          CLAIMS_SCHEMA_LOC,
      )
      .load(CLAIMS_METADATA_PATH)
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
      .option("cloudFiles.schemaLocation", TRAINING_SCHEMA_LOC)
      .load(TRAINING_BASE_PATH)
  )