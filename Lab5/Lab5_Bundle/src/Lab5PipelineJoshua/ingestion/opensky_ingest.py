import requests
import logging
from datetime import datetime, timezone
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, LongType, BooleanType
)
from pyspark.sql.functions import current_timestamp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenSkyIngestion")

def ingest_opensky_data():
    spark = SparkSession.builder.getOrCreate()

    print("==================================================")
    print(">>> [INGESTION TASK] STARTING OPENSKY INGESTION JOB")
    print("==================================================")

    # 1. Fetch data from OpenSky REST API with timeout
    url = "https://opensky-network.org/api/states/all"
    logger.info(f"Fetching data from OpenSky API: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to OpenSky API: {e}")
        raise

    data = response.json()
    states = data.get("states", [])
    
    if not states:
        logger.warning("No flight state data returned from OpenSky API.")
        return

    # 2. Define schema matching OpenSky state vector fields
    schema = StructType([
        StructField("icao24", StringType(), True),
        StructField("callsign", StringType(), True),
        StructField("origin_country", StringType(), True),
        StructField("time_position", LongType(), True),
        StructField("last_contact", LongType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("baro_altitude", DoubleType(), True),
        StructField("on_ground", BooleanType(), True),
        StructField("velocity", DoubleType(), True),
        StructField("true_track", DoubleType(), True),
        StructField("vertical_rate", DoubleType(), True),
        StructField("sensors", StringType(), True),
        StructField("geo_altitude", DoubleType(), True),
        StructField("squawk", StringType(), True),
        StructField("spi", BooleanType(), True),
        StructField("position_source", LongType(), True)
    ])

    # Clean and truncate rows to match the 17 expected columns
    cleaned_states = [row[:17] for row in states if row is not None]

    # 3. Create Spark DataFrame and add ingestion timestamp
    df = spark.createDataFrame(cleaned_states, schema=schema)
    df_bronze = df.withColumn("ingestion_timestamp", current_timestamp())

    # 4. Resolve target Catalog and Schema dynamically from Spark configuration (with sandbox fallbacks)
    # catalog = spark.conf.get("spark.lab5.catalog", "workspace")
    # bronze_schema = spark.conf.get("spark.lab5.bronze_schema", "default")
    try:
        catalog = spark.conf.get("spark.lab5.catalog")
    except Exception:
        catalog = "workspace"

    try:
        bronze_schema = spark.conf.get("spark.lab5.bronze_schema")
    except Exception:
        bronze_schema = "lab5_bronze" # Defaults to lab5_bronze instead of default so it matches your DLT expectations!

    table_name = f"{catalog}.{bronze_schema}.bronze_opensky_flights"
    
    # Ensure schema exists before writing
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{bronze_schema}")
    
    table_name = f"{catalog}.{bronze_schema}.bronze_opensky_flights"

    # 5. Write to Bronze Delta table (Append mode)
    logger.info(f"Writing {len(cleaned_states)} records to Delta table: {table_name}")
    df_bronze.write \
        .format("delta") \
        .mode("append") \
        .saveAsTable(table_name)
        
    logger.info("OpenSky ingestion completed successfully.")

if __name__ == "__main__":
    ingest_opensky_data()

# import requests
# import logging
# from datetime import datetime, timezone
# from pyspark.sql import SparkSession
# from pyspark.sql.types import (
#     StructType, StructField, StringType, DoubleType, LongType, BooleanType
# )
# from pyspark.sql.functions import current_timestamp

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("OpenSkyIngestion")

# def ingest_opensky_data():
#     spark = SparkSession.builder.getOrCreate()

#     # 1. Fetch data from OpenSky REST API with timeout
#     url = "https://opensky-network.org/api/states/all"
#     logger.info(f"Fetching data from OpenSky API: {url}")
    
#     try:
#         response = requests.get(url, timeout=30)
#         response.raise_for_status()
#     except requests.exceptions.RequestException as e:
#         logger.error(f"Failed to connect to OpenSky API: {e}")
#         raise

#     data = response.json()
#     states = data.get("states", [])
    
#     if not states:
#         logger.warning("No flight state data returned from OpenSky API.")
#         return

#     # 2. Define schema matching OpenSky state vector fields
#     schema = StructType([
#         StructField("icao24", StringType(), True),
#         StructField("callsign", StringType(), True),
#         StructField("origin_country", StringType(), True),
#         StructField("time_position", LongType(), True),
#         StructField("last_contact", LongType(), True),
#         StructField("longitude", DoubleType(), True),
#         StructField("latitude", DoubleType(), True),
#         StructField("baro_altitude", DoubleType(), True),
#         StructField("on_ground", BooleanType(), True),
#         StructField("velocity", DoubleType(), True),
#         StructField("true_track", DoubleType(), True),
#         StructField("vertical_rate", DoubleType(), True),
#         StructField("sensors", StringType(), True),
#         StructField("geo_altitude", DoubleType(), True),
#         StructField("squawk", StringType(), True),
#         StructField("spi", BooleanType(), True),
#         StructField("position_source", LongType(), True)
#     ])

#     # Clean and truncate rows to match the 17 expected columns
#     cleaned_states = [row[:17] for row in states if row is not None]

#     # 3. Create Spark DataFrame and add ingestion timestamp
#     df = spark.createDataFrame(cleaned_states, schema=schema)
#     df_bronze = df.withColumn("ingestion_timestamp", current_timestamp())

#     # 4. Resolve target Catalog and Schema dynamically from Spark configuration (with sandbox fallbacks)
#     catalog = spark.conf.get("spark.lab5.catalog", "workspace")
#     bronze_schema = spark.conf.get("spark.lab5.bronze_schema", "default")
#     table_name = f"{catalog}.{bronze_schema}.bronze_opensky_flights"

#     # 5. Write to Bronze Delta table (Append mode)
#     logger.info(f"Writing {len(cleaned_states)} records to Delta table: {table_name}")
#     df_bronze.write \
#         .format("delta") \
#         .mode("append") \
#         .saveAsTable(table_name)
        
#     logger.info("OpenSky ingestion completed successfully.")

# if __name__ == "__main__":
#     ingest_opensky_data()