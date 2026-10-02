from pyspark.sql.functions import (
    col, to_date, date_format, trim, initcap,
    split, size, when, concat, lit, abs, to_timestamp, regexp_extract
)

catalog = "dbr_dev"
bronze_schema = "joshuandegwa_bronze"
silver_schema = "joshuandegwa_silver"

# --- CLEAN TELEMATICS ---
@dlt.table(
    name=f"{catalog}.{silver_schema}.telemetry",
    comment="cleaned telematics events",
    table_properties={"quality": "silver"}
)
@dlt.expect("valid_coordinates", "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180")
def telemetry():
    return (
        dlt.readStream(f"{catalog}.{bronze_schema}.telemetry")
        .withColumn("event_timestamp", to_timestamp(col("event_timestamp"), "yyyy-MM-dd HH:mm:ss"))
        .drop("_rescued_data")
    )

# --- CLEAN POLICY ---
@dlt.table(
    name=f"{catalog}.{silver_schema}.policies",
    comment="Cleaned policies",
    table_properties={"quality": "silver"}
)
@dlt.expect("valid_policy_no", "policy_no IS NOT NULL")
def policy():
    return (
        dlt.readStream(f"{catalog}.{bronze_schema}.policies")
        .withColumn("premium", abs(col("premium")))  # Fixed abs() syntax
        .drop("_rescued_data")
    )

# --- CLEAN CLAIM ---
@dlt.table(
    name=f"{catalog}.{silver_schema}.claims",
    comment="Cleaned claims",
    table_properties={"quality": "silver"}
)
@dlt.expect_all({
    "valid_claim_number": "claim_no IS NOT NULL",
    "hour": "hour BETWEEN 0 AND 23"
})
def claim():
    df = dlt.readStream(f"{catalog}.{bronze_schema}.claims")
    return (
        df.withColumn("claim_date", to_date(col("claim_date")))
        .withColumn("incident_date", to_date(col("date"), "yyyy-MM-dd"))
        .withColumn("license_issue_date", to_date(col("license_issue_date"), "dd-MM-yyyy"))
        .drop("_rescued_data")
    )

# --- CLEAN CUSTOMER ---
@dlt.table(
    name=f"{catalog}.{silver_schema}.customer",
    comment="Cleaned customers (split names, minimal checks, drop name)",
    table_properties={"quality": "silver"}
)
@dlt.expect_all({
    "valid_customer_id": "customer_id IS NOT NULL"
})
def customer():
    df = dlt.readStream(f"{catalog}.{bronze_schema}.customers")

    name_normalized = when(
        size(split(trim(col("name")), ",")) == 2,
        concat(
            initcap(trim(split(col("name"), ",").getItem(1))), lit(" "),
            initcap(trim(split(col("name"), ",").getItem(0)))
        )
    ).otherwise(initcap(trim(col("name"))))

    return (
        df
        .withColumn("date_of_birth", to_date(col("date_of_birth"), "dd-MM-yyyy"))
        .withColumn("firstname", split(name_normalized, " ").getItem(0))
        .withColumn("lastname", split(name_normalized, " ").getItem(1))
        .withColumn("address", concat(col("BOROUGH"), lit(", "), col("ZIP_CODE"))) # Watch case sensitivity here
        .drop("name", "_rescued_data")
    )

# --- CLEAN TRAINING IMAGES ---
@dlt.table(
    name=f"{catalog}.{silver_schema}.training_images",
    comment="Enriched accident training images",
    table_properties={"quality": "silver"}
)
def training_images():
    df = dlt.readStream(f"{catalog}.{bronze_schema}.training_images")
    return df.withColumn(
        "label",
        regexp_extract("path", r"/(\d+)-([a-zA-Z]+)(?: \(\d+\))?\.png$", 2)
    )

# --- CLEAN CLAIM IMAGES ---
@dlt.table(
    name=f"{catalog}.{silver_schema}.claim_images",
    comment="Enriched claim images",
    table_properties={"quality": "silver"}
)
def claim_images():  # Fixed duplicate function name
    df = dlt.readStream(f"{catalog}.{bronze_schema}.claim_images")
    return df.withColumn("image_name", regexp_extract(col("path"), r".*/(.*?.jpg)", 1))