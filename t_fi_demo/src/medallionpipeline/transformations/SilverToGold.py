import geopy
import pandas as pd
from pyspark.sql.functions import col, lit, concat, pandas_udf, avg
from typing import Iterator
import random

catalog = "dbr_dev"
silver_schema = "joshuandegwa_silver"
gold_schema = "joshuandegwa_gold"

def geocode(geolocator, address):
    try:
        # Mock generator for fast demo testing
        return pd.Series({'latitude': random.uniform(-90, 90), 'longitude': random.uniform(-180, 180)})
    except Exception as e:
        print(f"error getting lat/long: {e}")
    return pd.Series({'latitude': None, 'longitude': None})
      
@pandas_udf("struct<latitude: float, longitude: float>")
def get_lat_long(batch_iter: Iterator[pd.Series]) -> Iterator[pd.DataFrame]:
  geolocator = geopy.Nominatim(user_agent="claim_lat_long", timeout=5, scheme='https')
  for address in batch_iter:
    yield address.apply(lambda x: geocode(geolocator, x))

# --- AGGREGATED TELEMATICS ---
@dlt.table(
    name=f"{catalog}.{gold_schema}.aggregated_telematics",
    comment="Average telematics",
    table_properties={"quality": "gold"}
)
def aggregated_telematics():
    return (
        dlt.read(f"{catalog}.{silver_schema}.telemetry")  # Matched silver table name: telemetry
        .groupBy("chassis_no")
        .agg(
            avg("speed").alias("telematics_speed"),
            avg("latitude").alias("telematics_latitude"),
            avg("longitude").alias("telematics_longitude"),
        )
    )

# --- CLAIM-POLICY ---
@dlt.table(
    name=f"{catalog}.{gold_schema}.customer_claim_policy",
    comment="Curated claim joined with policy records",
    table_properties={"quality": "gold"}
)
def customer_claim_policy():
    # Read dimension tables and drop metadata columns to avoid collisions
    policies = dlt.read(f"{catalog}.{silver_schema}.policies").drop("__START_AT", "__END_AT")
    customer = dlt.read(f"{catalog}.{silver_schema}.customer").drop("__START_AT", "__END_AT")
    
    # Stream the fact table and drop metadata columns too
    claims = dlt.readStream(f"{catalog}.{silver_schema}.claims").drop("__START_AT", "__END_AT")
    
    claim_policy = claims.join(policies, "policy_no")
    return claim_policy.join(customer, claim_policy.cust_id == customer.customer_id)

# --- CLAIM-POLICY-TELEMATICS ---
@dlt.table(
    name=f"{catalog}.{gold_schema}.customer_claim_policy_telematics",
    comment="claims with geolocation latitude/longitude",
    table_properties={"quality": "gold"}
)
def customer_claim_policy_telematics():
    telematics = dlt.read(f"{catalog}.{gold_schema}.aggregated_telematics")
    customer_claim_policy = dlt.read(f"{catalog}.{gold_schema}.customer_claim_policy").where("address is not null")
    
    return (
        customer_claim_policy
        .withColumn("lat_long", get_lat_long(col("address")))
        .join(telematics, on="chassis_no", how="left")
    )