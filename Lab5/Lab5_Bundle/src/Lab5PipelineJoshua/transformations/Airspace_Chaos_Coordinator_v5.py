from pyspark import pipelines as dp
from pyspark.sql import functions as F

# Lab 5 — Flight Stream Lakeflow Declarative Pipeline
# CATALOG        = spark.conf.get("catalog")
# BRONZE_SCHEMA  = spark.conf.get("bronze_schema")
# SILVER_SCHEMA  = spark.conf.get("silver_schema")
# GOLD_SCHEMA    = spark.conf.get("gold_schema")

CATALOG       = spark.conf.get("catalog", "workspace")
BRONZE_SCHEMA  = spark.conf.get("bronze_schema", "lab5_bronze")
SILVER_SCHEMA  = spark.conf.get("silver_schema", "lab5_silver")
GOLD_SCHEMA    = spark.conf.get("gold_schema", "lab5_gold")

# Distinct table namespace dictionary
TABLES = {
    "raw_flights_stream": "raw_flights_stream",
    "clean_flights_stream": "clean_flights_stream",
    "dedup_flights": "dedup_flights",
    "gold_hourly_airspace_metrics": "gold_hourly_airspace_metrics",
    "gold_origin_country_summary": "gold_origin_country_summary",
    "gold_callsign_leaderboard": "gold_callsign_leaderboard"
}

# ==============================================
# BRONZE LAYER — Streaming Source
# ==============================================

@dp.table(name=TABLES["raw_flights_stream"])
def raw_flights_stream():
    # select * from workspace.default.bronze_opensky_flights limit 10; 
    return spark.readStream.table(f"{CATALOG}.{BRONZE_SCHEMA}.bronze_opensky_flights")


# ==============================================
# SILVER LAYER — Filtering, Cleaning & Auto-CDC
# ==============================================

@dp.table(name=TABLES["clean_flights_stream"])
# Mode 1: Drop completely invalid or grounded rows
@dp.expect_all_or_drop({
    "valid_identifier": "icao24 IS NOT NULL",
    "valid_coordinates": "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180",
    "airborne_only": "on_ground = false"
})
# Mode 2: Log warnings for suspicious telemetry without dropping the row
@dp.expect_all({
    "suspicious_high_speed": "velocity <= 350.0"
})
def clean_flights_stream():
    return (
        spark.readStream.table(TABLES["raw_flights_stream"])
        # String cleanups
        .withColumn("callsign", F.trim(F.col("callsign")))
        .withColumn("origin_country", F.trim(F.col("origin_country")))
        .withColumn("squawk", F.coalesce(F.trim(F.col("squawk")), F.lit("UNKNOWN")))
        # Numeric & coordinate type safety
        .withColumn("baro_altitude", F.col("baro_altitude").cast("double"))
        .withColumn("geo_altitude", F.col("geo_altitude").cast("double"))
        .withColumn("velocity", F.col("velocity").cast("double"))
        .withColumn("latitude", F.col("latitude").cast("double"))
        .withColumn("longitude", F.col("longitude").cast("double"))
        # Flag and source type safety
        .withColumn("spi", F.col("spi").cast("boolean"))
        .withColumn("position_source", F.col("position_source").cast("int"))
    )

# Automated CDC / Deduplication on icao24 keeping latest position update
dp.create_streaming_table(TABLES["dedup_flights"])
dp.create_auto_cdc_flow(
    target      = TABLES["dedup_flights"],
    source      = TABLES["clean_flights_stream"],
    keys        = ["icao24"],
    sequence_by = F.col("ingestion_timestamp"),
)


# =============================================
# GOLD LAYER — Aggregated Analytics & Summaries
# =============================================

# 1. Hourly airspace metrics broken down by country and flight altitude brackets
@dp.materialized_view(name=f"{CATALOG}.{GOLD_SCHEMA}.gold_hourly_airspace_metrics")
def gold_hourly_airspace_metrics():
    return spark.sql(f"""
        SELECT 
            origin_country,
            DATE(ingestion_timestamp) AS flight_date,
            HOUR(ingestion_timestamp) AS flight_hour,
            CASE 
                WHEN baro_altitude < 3048 THEN 'Low (< 10k ft)'
                WHEN baro_altitude BETWEEN 3048 AND 9144 THEN 'Medium (10k-30k ft)'
                ELSE 'High (> 30k ft)'
            END AS altitude_bracket,
            COUNT(DISTINCT icao24) AS unique_aircraft_count,
            ROUND(AVG(baro_altitude), 2) AS average_altitude,
            ROUND(MAX(velocity), 2) AS peak_velocity
        FROM {TABLES["dedup_flights"]}
        GROUP BY origin_country, DATE(ingestion_timestamp), HOUR(ingestion_timestamp), altitude_bracket
    """)

# 2. Origin summary dimension aggregating total tracked volume per country
@dp.materialized_view(name=f"{CATALOG}.{GOLD_SCHEMA}.gold_origin_country_summary")
def gold_origin_country_summary():
    return spark.sql(f"""
        SELECT 
            origin_country,
            COUNT(*) AS total_sightings,
            CURRENT_TIMESTAMP() AS last_updated
        FROM {TABLES["dedup_flights"]}
        GROUP BY origin_country
    """)

# 3. Active callsign activity leaderboard
@dp.materialized_view(name=f"{CATALOG}.{GOLD_SCHEMA}.gold_callsign_leaderboard")
def gold_callsign_leaderboard():
    return spark.sql(f"""
        SELECT 
            callsign,
            origin_country,
            COUNT(*) AS position_updates_count,
            ROUND(AVG(velocity), 2) AS avg_velocity,
            MAX(ingestion_timestamp) AS last_seen
        FROM {TABLES["dedup_flights"]}
        WHERE callsign != '' AND callsign IS NOT NULL
        GROUP BY callsign, origin_country
        ORDER BY position_updates_count DESC
    """)
    
    # ==========================================
# LAB 6: STAR SCHEMA (GOLD LAYER) EXTENSIONS
# ==========================================

@dp.materialized_view(
    name=f"{CATALOG}.{GOLD_SCHEMA}.gold_dim_aircraft",
    comment="Dimension table for unique aircraft and callsigns"
)
def gold_dim_aircraft():
    df = spark.read.table(TABLES["dedup_flights"])
    return df.select("icao24", "callsign").dropDuplicates(["icao24"])


@dp.materialized_view(
    name=f"{CATALOG}.{GOLD_SCHEMA}.gold_dim_country",
    comment="Dimension table for origin countries"
)
def gold_dim_country():
    df = spark.read.table(TABLES["dedup_flights"])
    return df.select(
        F.col("origin_country").alias("country_code")
    ).dropDuplicates(["country_code"])


@dp.materialized_view(
    name=f"{CATALOG}.{GOLD_SCHEMA}.gold_fact_flight_observations",
    comment="Fact table containing granular flight state metrics and measurements"
)
def gold_fact_flight_observations():
    df = spark.read.table(TABLES["dedup_flights"])
    return df.select(
        "icao24",
        "callsign",
        F.col("origin_country").alias("country_code"),
        "baro_altitude",
        "velocity",
        "vertical_rate",
        "on_ground",
        F.col("ingestion_timestamp").alias("observation_timestamp")
    )