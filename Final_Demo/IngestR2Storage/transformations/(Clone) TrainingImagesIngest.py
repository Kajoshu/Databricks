import dlt

base_path = "r2://smart-claims-bucket@8d6974c4eec2dd94eaeb74af884b60d9.r2.cloudflarestorage.com/training_img"

@dlt.table(
    name="dbr_dev.joshuandegwa_bronze.training_images", 
    comment="Raw training images ingested from Cloudflare R2 via Auto Loader (No archiving)", 
    table_properties={"quality": "bronze"}
)
def training_images():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "binaryFile")
        .option("cloudFiles.schemaLocation", f"{base_path}/_schemas/training_images_schema")
        .load(f"{base_path}/images")
    )
