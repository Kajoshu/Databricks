import dlt
from pyspark.sql.functions import col, current_timestamp, from_json, struct
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

# 1. Confluent Cloud Connection Parameters
CONFLUENT_BOOTSTRAP = "pkc-921jm.us-east-2.aws.confluent.cloud:9092"
CONFLUENT_API_KEY = "443GI6WDMGYIYHYD"
CONFLUENT_API_SECRET = (
    "cfltvgM+Ukf0dlkXLSyOyxLOFB6mclAITEyKW4OJjofB64y2HKCw3z1gYQYKStyQ"
)
TOPIC_NAME = "telemetry-stream"

# 2. Define the schema matching your telemetry payload data
telemetry_schema = StructType([
    StructField("chassis_no", StringType(), True),
    StructField("latitude", DoubleType(), True),
    StructField("longitude", DoubleType(), True),
    StructField("event_timestamp", StringType(), True),
    StructField("speed", DoubleType(), True),
])


@dlt.table(
    name="telemetry",
    comment=(
        "Parsed Confluent Kafka telemetry data with embedded metadata struct"
    ),
    table_properties={"quality": "bronze"},
)
def telemetry_landing():
  # 3. Read stream using flattened Kafka options for serverless compatibility
  raw_stream = (
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

  # 4. Extract Kafka native metadata and parse payload JSON
  parsed_stream = (
      raw_stream.selectExpr(
          "CAST(value AS STRING) AS raw_json",
          "key AS message_key",
          "topic",
          "partition",
          "offset",
          "timestamp AS kafka_ingest_time",
      )
      .withColumn("decoded_data", from_json(col("raw_json"), telemetry_schema))
      .withColumn(
          "stream_metadata",
          struct(
              col("message_key"),
              col("topic"),
              col("partition"),
              col("offset"),
              col("kafka_ingest_time"),
          ),
      )
  )

  # 5. Project final columns matching your desired schema and add processing timestamp
  return parsed_stream.select(
      col("decoded_data.chassis_no"),
      col("decoded_data.latitude"),
      col("decoded_data.longitude"),
      col("decoded_data.event_timestamp"),
      col("decoded_data.speed"),
      col("stream_metadata"),
      current_timestamp().alias("ingestion_time"),
  )