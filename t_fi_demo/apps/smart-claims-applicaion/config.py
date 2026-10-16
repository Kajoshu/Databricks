"""Centralized configuration for Smart Claims app.

All environment-specific values live here so nothing is hardcoded
across page files, utilities, or components.
"""

# ── Lakebase Postgres ─────────────────────────────────────────────────
LAKEBASE_ENDPOINT = "projects/smart-claims/branches/production/endpoints/primary"
LAKEBASE_DB_NAME = "databricks_postgres"

# ── Lakebase Schemas / Tables (Postgres side) ────────────────────────
CLAIMS_SYNCED_TABLE = "smart_claims.claims_synced"
RULES_SYNCED_TABLE = "smart_claims.claims_rules_synced"
ACTIONS_TABLE = "public.claim_actions"
ADMIN_USERS_TABLE = "public.admin_users"

# ── Model Serving ─────────────────────────────────────────────────────
SERVING_ENDPOINT_NAME = "claims_damage_level"

# ── Unity Catalog (Delta / Volumes) ──────────────────────────────────
GOLD_TABLE = "dbr_dev.joshuandegwa_gold.customer_claim_policy_telematics_predicted"
CLAIM_IMAGES_VOLUME = "/Volumes/dbr_dev/joshuandegwa_bronze/images/claims/images"

# ── Rule Engine Thresholds ───────────────────────────────────────────
SPEED_LIMIT_KMH = 45

# ── App Settings ─────────────────────────────────────────────────────
MAX_UPLOAD_MB = 200
ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png"]
CLAIMS_LIST_LIMIT = 50
