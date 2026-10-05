import os
import sys
import mlflow
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr, struct

# Ensure conf.py (in the same /src directory) is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conf import CATALOG, GOLD_SCHEMA, SILVER_SCHEMA

# Initialize Spark session
spark = SparkSession.builder.getOrCreate()

print("--- 1. Running Silver Ingestion Layer Verification ---")
gold_table = f"{CATALOG}.{GOLD_SCHEMA}.customer_claim_policy_telematics"
gold_df = spark.read.table(gold_table)

print("--- 2. Running ML Model Inference via Spark UDF ---")
# Reference your registered model in Unity Catalog
model_uri = f"models:/{CATALOG}.{GOLD_SCHEMA}.claims_damage_level@champion"

# Load model as a native Spark UDF
# This distributes predictions efficiently across the cluster workers
loaded_model_udf = mlflow.pyfunc.spark_udf(spark, model_uri=model_uri)  # Ensure environment dependencies are met or replace with a compatible model URI.

# Score incoming records by passing the relevant dataframe columns into the model UDF
# (struct(*map(col, gold_df.columns)) passes all columns, or specify exact feature columns)
scored_df = gold_df.withColumn(
    "predicted_damage_score", 
    loaded_model_udf(struct(*map(col, gold_df.columns)))
)

print("--- 3. Executing Dynamic Rules Engine ---")
df = scored_df

rules = spark.sql(f"SELECT * FROM {CATALOG}.{SILVER_SCHEMA}.claims_rules WHERE is_active=true ORDER BY rule_id").collect()
for rule in rules:
    df = df.withColumn(rule.check_name, expr(rule.check_code))

print("--- 4. Materializing Final Gold Insights Table ---")
df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{CATALOG}.{GOLD_SCHEMA}.claim_insights")

print("--- E2E Pipeline Complete! ---")