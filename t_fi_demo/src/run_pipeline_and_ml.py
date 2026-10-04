import mlflow
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr, struct

# Initialize Spark session
spark = SparkSession.builder.getOrCreate()

print("--- 1. Running Silver Ingestion Layer Verification ---")
gold_table = "dbr_dev.joshuandegwa_gold.customer_claim_policy_telematics"
gold_df = spark.read.table(gold_table)

print("--- 2. Running ML Model Inference via Spark UDF ---")
# Reference your registered model in Unity Catalog
model_uri = "models:/dbr_dev.joshuandegwa_gold.claims_damage_level/2"

# Load model as a native Spark UDF
# This distributes predictions efficiently across the cluster workers
loaded_model_udf = mlflow.pyfunc.spark_udf(spark, model_uri=model_uri)  # Ensure environment dependencies are met or replace with a compatible model URI.

# Score incoming records by passing the relevant dataframe columns into the model UDF
# (struct(*map(col, gold_df.columns)) passes all columns, or specify exact feature columns)
scored_df = gold_df.withColumn(
    "predicted_damage_score", 
    loaded_model_udf(struct(*map(col, gold_df.columns)))
)

# --- UDF smoke-test: run the model on 5 rows before committing any write ---
print("--- UDF smoke-test: scoring 5 rows ---")
(
    scored_df
    .select("predicted_damage_score")
    .limit(5)
)
print(f"Prediction column type: {dict(scored_df.dtypes)['predicted_damage_score']}")

print("--- 3. Executing Dynamic Rules Engine ---")
df = spark.sql("SELECT * FROM dbr_dev.joshuandegwa_gold.customer_claim_policy_telematics_predicted")

rules = spark.sql("SELECT * FROM dbr_dev.joshuandegwa_silver.claims_rules WHERE is_active=true ORDER BY rule_id").collect()
for rule in rules:
    df = df.withColumn(rule.check_name, expr(rule.check_code))

print("--- 4. Materializing Final Gold Insights Table ---")
df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("dbr_dev.joshuandegwa_gold.claim_insights")

print("--- E2E Pipeline Complete! ---")