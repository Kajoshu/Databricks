# import dlt

# # Define R2 base path and subpaths using your Cloudflare account ID and bucket
# base_path = "r2://smart-claims-bucket@8d6974c4eec2dd94eaeb74af884b60d9.r2.cloudflarestorage.com/claims"
# source_path = f"{base_path}/images"
# archive_path = f"{base_path}/archive"

# # Archive configs to automatically move processed files after 1 minute
# archive_configs = {
#     "cloudFiles.cleanSource": "MOVE",
#     "cloudFiles.cleanSource.retentionDuration": "1 minute",
#     "cloudFiles.cleanSource.moveDestination": archive_path
# }

# # Read incoming binary image files using Auto Loader with R2 metadata paths
# @dlt.table(
#     name="dbr_dev.joshuandegwa_bronze.claim_images",
#     comment="Raw claim images ingested from Cloudflare R2 via Auto Loader",
#     table_properties={"quality": "bronze"},
# )
# def claim_images():
#     return (
#         spark.readStream
#         .format("cloudFiles")
#         .option("cloudFiles.format", "binaryFile")
#         .options(**archive_configs)
#         .load(source_path)
#     )