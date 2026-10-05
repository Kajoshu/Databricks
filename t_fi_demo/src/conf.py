import os

# --- Environment & Naming Variables ---
# Override these using environment variables or Databricks bundle parameters.
CATALOG        = os.getenv("DBR_CATALOG", "dbr_dev")
BRONZE_SCHEMA  = os.getenv("DBR_BRONZE_SCHEMA", "joshuandegwa_bronze")
SILVER_SCHEMA  = os.getenv("DBR_SILVER_SCHEMA", "joshuandegwa_silver")
GOLD_SCHEMA    = os.getenv("DBR_GOLD_SCHEMA",   "joshuandegwa_gold")

# --- Base Volume Paths ---
VOLUME_BASE = f"/Volumes/{CATALOG}/{BRONZE_SCHEMA}"

# --- Claims Paths ---
CLAIMS_BASE_PATH = f"{VOLUME_BASE}/images/claims"
CLAIMS_INCOMING = f"{CLAIMS_BASE_PATH}/images"
CLAIMS_ARCHIVE = f"{CLAIMS_BASE_PATH}/archive"
CLAIMS_METADATA_PATH = f"{CLAIMS_BASE_PATH}/metadata"
CLAIMS_SCHEMA_LOC = f"{CLAIMS_BASE_PATH}/_schemas/claim_metadata_schema"

# --- Confluent / Kafka ---
CONFLUENT_BOOTSTRAP  = os.getenv("CONFLUENT_BOOTSTRAP", "pkc-921jm.us-east-2.aws.confluent.cloud:9092")
CONFLUENT_TOPIC_NAME = os.getenv("CONFLUENT_TOPIC_NAME", "telemetry-stream")
# Credentials: set via Databricks Secrets — never hardcode values here.
CONFLUENT_API_KEY    = os.getenv("CONFLUENT_API_KEY", "")
CONFLUENT_API_SECRET = os.getenv("CONFLUENT_API_SECRET", "")

# --- Training Images Paths ---
# Images are uploaded directly into training_imgs/.
# Schema location sits outside the load path to avoid Auto Loader ingesting it.
TRAINING_BASE_PATH = f"{VOLUME_BASE}/images/training_imgs"
TRAINING_SCHEMA_LOC = f"{VOLUME_BASE}/images/training_imgs/_schemas/training_images_schema"
