"""Centralized project configuration for t_fi_demo.

Every notebook, pipeline, and the Streamlit app should import from here
instead of hardcoding catalog names, table paths, credentials, or thresholds.

Credentials are fetched at runtime via dbutils.secrets (notebooks/pipelines)
or environment variables (Databricks App). NEVER hardcode API keys.
"""

# ═══════════════════════════════════════════════════════════════════════
#  Unity Catalog — Catalog & Schemas
# ═══════════════════════════════════════════════════════════════════════
UC_CATALOG = "dbr_dev"

SCHEMA_BRONZE = "joshuandegwa_bronze"
SCHEMA_SILVER = "joshuandegwa_silver"
SCHEMA_GOLD = "joshuandegwa_gold"

FQ_SCHEMA_BRONZE = f"{UC_CATALOG}.{SCHEMA_BRONZE}"
FQ_SCHEMA_SILVER = f"{UC_CATALOG}.{SCHEMA_SILVER}"
FQ_SCHEMA_GOLD = f"{UC_CATALOG}.{SCHEMA_GOLD}"

# ═══════════════════════════════════════════════════════════════════════
#  Bronze Tables
# ═══════════════════════════════════════════════════════════════════════
BRONZE_CLAIMS = f"{FQ_SCHEMA_BRONZE}.claims"
BRONZE_CUSTOMERS = f"{FQ_SCHEMA_BRONZE}.customers"
BRONZE_POLICIES = f"{FQ_SCHEMA_BRONZE}.policies"
BRONZE_TELEMETRY = f"{FQ_SCHEMA_BRONZE}.telemetry"
BRONZE_CLAIM_IMAGES = f"{FQ_SCHEMA_BRONZE}.claim_images"
BRONZE_CLAIM_METADATA = f"{FQ_SCHEMA_BRONZE}.claim_metadata"
BRONZE_TRAINING_IMAGES = f"{FQ_SCHEMA_BRONZE}.training_images"

# ═══════════════════════════════════════════════════════════════════════
#  Silver Tables
# ═══════════════════════════════════════════════════════════════════════
SILVER_CLAIMS = f"{FQ_SCHEMA_SILVER}.claims"
SILVER_CUSTOMER = f"{FQ_SCHEMA_SILVER}.customer"
SILVER_POLICIES = f"{FQ_SCHEMA_SILVER}.policies"
SILVER_TELEMETRY = f"{FQ_SCHEMA_SILVER}.telemetry"
SILVER_CLAIM_IMAGES = f"{FQ_SCHEMA_SILVER}.claim_images"
SILVER_CLAIMS_RULES = f"{FQ_SCHEMA_SILVER}.claims_rules"
SILVER_TRAINING_IMAGES = f"{FQ_SCHEMA_SILVER}.training_images"
SILVER_TRAINING_IMAGES_RESIZED = f"{FQ_SCHEMA_SILVER}.training_images_resized"

# ═══════════════════════════════════════════════════════════════════════
#  Gold Tables
# ═══════════════════════════════════════════════════════════════════════
GOLD_CUSTOMER_CLAIM_POLICY = f"{FQ_SCHEMA_GOLD}.customer_claim_policy"
GOLD_CUSTOMER_CLAIM_POLICY_TELEMATICS = f"{FQ_SCHEMA_GOLD}.customer_claim_policy_telematics"
GOLD_CUSTOMER_CLAIM_POLICY_TELEMATICS_PREDICTED = f"{FQ_SCHEMA_GOLD}.customer_claim_policy_telematics_predicted"
GOLD_AGGREGATED_TELEMATICS = f"{FQ_SCHEMA_GOLD}.aggregated_telematics"
GOLD_CLAIM_IMAGES_PREDICTED = f"{FQ_SCHEMA_GOLD}.claim_images_predicted"
GOLD_CLAIM_IMAGES_FOR_REVIEW = f"{FQ_SCHEMA_GOLD}.claim_images_for_review"
GOLD_CLAIM_INSIGHTS = f"{FQ_SCHEMA_GOLD}.claim_insights"
GOLD_DAMAGE_PREDICTIONS = f"{FQ_SCHEMA_GOLD}.damage_predictions"
GOLD_TRAINING_IMAGES_FOR_REVIEW = f"{FQ_SCHEMA_GOLD}.training_images_for_review"

# ═══════════════════════════════════════════════════════════════════════
#  UC Volumes — Images
# ═══════════════════════════════════════════════════════════════════════
CLAIM_IMAGES_VOLUME = f"/Volumes/{UC_CATALOG}/{SCHEMA_BRONZE}/images/claims/images"
TRAINING_IMAGES_VOLUME = f"/Volumes/{UC_CATALOG}/{SCHEMA_BRONZE}/images/training_img"

# ═══════════════════════════════════════════════════════════════════════
#  Cloudflare R2 Storage
# ═══════════════════════════════════════════════════════════════════════
R2_ACCOUNT_ID = "8d6974c4eec2dd94eaeb74af884b60d9"
R2_BUCKET_NAME = "smart-claims-bucket"
R2_BASE_URL = f"r2://{R2_BUCKET_NAME}@{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
R2_CLAIMS_PATH = f"{R2_BASE_URL}/claims"
R2_TRAINING_IMG_PATH = f"{R2_BASE_URL}/training_img"

# ═══════════════════════════════════════════════════════════════════════
#  Confluent Cloud (Kafka) — Telemetry Streaming
#  Credentials via Databricks Secrets: dbutils.secrets.get(scope, key)
# ═══════════════════════════════════════════════════════════════════════
CONFLUENT_BOOTSTRAP_SERVER = "pkc-921jm.us-east-2.aws.confluent.cloud:9092"
CONFLUENT_TOPIC = "telemetry-stream"
CONFLUENT_SECRET_SCOPE = "confluent"
CONFLUENT_SECRET_KEY_API_KEY = "api_key"
CONFLUENT_SECRET_KEY_API_SECRET = "api_secret"


def get_confluent_credentials(dbutils):
    """Retrieve Confluent API key + secret from Databricks Secrets.

    Usage in notebooks / pipelines:
        from project_config import get_confluent_credentials, CONFLUENT_BOOTSTRAP_SERVER
        creds = get_confluent_credentials(dbutils)
        # creds["api_key"], creds["api_secret"]
    """
    return {
        "api_key": dbutils.secrets.get(scope=CONFLUENT_SECRET_SCOPE, key=CONFLUENT_SECRET_KEY_API_KEY),
        "api_secret": dbutils.secrets.get(scope=CONFLUENT_SECRET_SCOPE, key=CONFLUENT_SECRET_KEY_API_SECRET),
    }


def get_kafka_options(dbutils):
    """Return a dict of Spark readStream options for Confluent Kafka.

    Usage:
        opts = get_kafka_options(dbutils)
        df = spark.readStream.format("kafka").options(**opts).load()
    """
    creds = get_confluent_credentials(dbutils)
    jaas = (
        'kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule'
        f' required username="{creds["api_key"]}" password="{creds["api_secret"]}";'
    )
    return {
        "kafka.bootstrap.servers": CONFLUENT_BOOTSTRAP_SERVER,
        "subscribe": CONFLUENT_TOPIC,
        "kafka.security.protocol": "SASL_SSL",
        "kafka.sasl.mechanism": "PLAIN",
        "kafka.sasl.jaas.config": jaas,
        "startingOffsets": "latest",
    }


# ═══════════════════════════════════════════════════════════════════════
#  ML Model & Serving
# ═══════════════════════════════════════════════════════════════════════
ML_MODEL_NAME = f"{UC_CATALOG}.{SCHEMA_GOLD}.claims_damage_level"
ML_MODEL_ALIAS = "prod"
ML_MODEL_URI = f"models:/{ML_MODEL_NAME}@{ML_MODEL_ALIAS}"
SERVING_ENDPOINT_NAME = "claims_damage_level"

# ═══════════════════════════════════════════════════════════════════════
#  Lakebase Postgres (Synced Tables)
# ═══════════════════════════════════════════════════════════════════════
LAKEBASE_ENDPOINT = "projects/smart-claims/branches/production/endpoints/primary"
LAKEBASE_DB_NAME = "databricks_postgres"
LAKEBASE_CLAIMS_TABLE = "smart_claims.claims_synced"
LAKEBASE_RULES_TABLE = "smart_claims.claims_rules_synced"
LAKEBASE_ACTIONS_TABLE = "public.claim_actions"

# ═══════════════════════════════════════════════════════════════════════
#  Rule Engine Thresholds
# ═══════════════════════════════════════════════════════════════════════
SPEED_LIMIT_MPH = 45

# Severity mapping: self-assessed severity → expected ML label
SEVERITY_TO_ML_LABEL = {
    "Total Loss": "major",
    "Major Damage": "minor",
    "Minor Damage": "minor",
    "Trivial Damage": "minor",
}

# ═══════════════════════════════════════════════════════════════════════
#  App Settings
# ═══════════════════════════════════════════════════════════════════════
MAX_UPLOAD_MB = 200
ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png"]
CLAIMS_LIST_LIMIT = 50
