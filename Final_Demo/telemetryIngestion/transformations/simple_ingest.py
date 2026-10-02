import dlt
from pyspark.sql.functions import col, current_timestamp, from_json
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

# 1. Confluent Cloud Connection Parameters
CONFLUENT_BOOTSTRAP = "pkc-921jm.us-east-2.aws.confluent.cloud:9092"
CONFLUENT_API_KEY = "443GI6WDMGYIYHYD"
CONFLUENT_API_SECRET = (
    "cfltvgM+Ukf0dlkXLSyOyxLOFB6mclAITEyKW4OJjofB64y2HKCw3z1gYQYKStyQ"
)
TOPIC_NAME = "telemetry-stream"

# 2. Define the schema matching your telemetry data
telemetry_schema = StructType([
    StructField("chassis_no", StringType(), True),
    StructField("latitude", DoubleType(), True),
    StructField("longitude", DoubleType(), True),
    StructField("event_timestamp", StringType(), True),
    StructField("speed", DoubleType(), True),
])


@dlt.table(
    name="telemetry_landing_simple",
    comment=(
        "Raw bronze telemetry stream ingested from Confluent Cloud Kafka via DLT"
    ),
    table_properties={"quality": "bronze"},
)
def telemetry_landing():
  # 3. Read stream using flattened Kafka options for serverless compatibility
  kafka_stream_df = (
      spark.readStream.format("kafka")
      .option("kafka.bootstrap.servers", CONFLUENT_BOOTSTRAP)
      .option("subscribe", TOPIC_NAME)
      .option("startingOffsets", "earliest")
      .option("failOnDataLoss", "false")
      .option("kafka.security.protocol", "SASL_SSL")
      .option("kafka.sasl.mechanism", "PLAIN")
      .option(
          "kafka.sasl.jaas.config",
          "kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule"
          f' required username="{CONFLUENT_API_KEY}" password="{CONFLUENT_API_SECRET}";',
      )
      .load()
  )

  # 4. Parse JSON value and add standard metadata enrichment columns
  df_enriched = (
      kafka_stream_df.select(
          from_json(col("value").cast("string"), telemetry_schema).alias(
              "data"
          ),
          col("timestamp").alias("kafka_ingest_time"),
      )
      .select("data.*", "kafka_ingest_time")
      .withColumn("ingestion_time", current_timestamp())
  )

  return df_enriched