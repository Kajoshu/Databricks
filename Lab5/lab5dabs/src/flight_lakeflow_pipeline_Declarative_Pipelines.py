# Databricks notebook source
# DBTITLE 1,Flight Lakeflow Declarative Pipeline
from pyspark import pipelines as dp
from pyspark.sql import functions as F

# Lab 5 — Flight Stream Lakeflow Declarative Pipeline
CATALOG        = spark.conf.get("CATALOG")
BRONZE_SCHEMA  = spark.conf.get("BRONZE_SCHEMA")
SILVER_SCHEMA  = spark.conf.get("SILVER_SCHEMA")
GOLD_SCHEMA    = spark.conf.get("GOLD_SCHEMA")

# Distinct table namespace dictionary
TABLES = {
    "raw_flights_stream": "raw_flights_stream",
    "clean_flights_stream": "clean_flights_stream",
    "dedup_flights": "dedup_flights",
    "airport_lookup_batch": "airport_lookup_batch",
    "gold_hourly_airspace_metrics": "gold_hourly_airspace_metrics",
    "gold_origin_country_summary": "gold_origin_country_summary"
}

# ==============================================
# BRONZE LAYER (Batch file source + Streaming source)
# ==============================================

# 1. Static reference data (Airports / Zones JSON)
# @dp.materialized_view(name=TABLES["airport_lookup_batch"])
# def airport_lookup_batch():
#     landing_path = f"/Volumes/{CATALOG}/{BRONZE_SCHEMA}/files/airports_reference.json"
#     return spark.read.format("json").load(landing_path)

# 2. Continuous streaming source from raw flight vectors
@dp.table(name=TABLES["raw_flights_stream"])
def raw_flights_stream():
    return spark.readStream.table(f"{CATALOG}.{BRONZE_SCHEMA}.bronze_opensky_flights")


# ==============================================
# SILVER LAYER — Expectations & Auto-CDC
# ==============================================

# Clean streaming flights + data quality checks
@dp.table(name=TABLES["clean_flights_stream"])
@dp.expect_all_or_drop({
    "valid_identifier": "icao24 IS NOT NULL",
    "valid_coordinates": "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180"
})
@dp.expect_all_or_drop({
    "reasonable_speed": "velocity <= 300.0", # Max realistic knot speed check for regional bounding box
})
def clean_flights_stream():
    return (
        spark.readStream.table(TABLES["raw_flights_stream"])
        .withColumn("baro_altitude", F.col("baro_altitude").cast("double"))
        .withColumn("velocity", F.col("velocity").cast("double"))
    )

# Automated CDC / Deduplication on icao24 keeping latest position update
dp.create_streaming_table(TABLES["dedup_flights"])
dp.create_auto_cdc_flow(
    target      = TABLES["dedup_flights"],
    source      = TABLES["clean_flights_stream"],
    keys        = ["icao24"],
    sequence_by = F.col("_api_snapshot_time"),
)


# =============================================
# GOLD LAYER — Aggregated Analytics & Summaries
# =============================================

# Hourly airspace metrics by country and altitude brackets
@dp.materialized_view(name=f"{CATALOG}.{GOLD_SCHEMA}.gold_hourly_airspace_metrics")
def gold_hourly_airspace_metrics():
    return spark.sql(f"""
        SELECT 
            origin_country,
            DATE(_api_snapshot_time) AS flight_date,
            HOUR(_api_snapshot_time) AS flight_hour,
            COUNT(DISTINCT icao24) AS unique_aircraft_count,
            ROUND(AVG(baro_altitude), 2) AS average_altitude,
            ROUND(MAX(velocity), 2) AS peak_velocity
        FROM {TABLES["dedup_flights"]}
        GROUP BY origin_country, DATE(_api_snapshot_time), HOUR(_api_snapshot_time)
    """)

# Origin summary dimension
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