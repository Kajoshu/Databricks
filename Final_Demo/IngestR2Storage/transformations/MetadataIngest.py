import dlt

base_path = "r2://smart-claims-bucket@8d6974c4eec2dd94eaeb74af884b60d9.r2.cloudflarestorage.com/claims"

@dlt.table(
    name="dbr_dev.joshuandegwa_bronze.claim_metadata",
    comment="Raw claim metadata CSV files ingested from Cloudflare R2 via Auto Loader", 
    table_properties={"quality": "bronze"}
)
def claim_metadata():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .option("cloudFiles.schemaLocation", f"{base_path}/metadata/image_metadata.csv")
        .load(f"{base_path}/metadata")
    )