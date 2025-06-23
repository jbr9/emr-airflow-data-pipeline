from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
from pyspark.sql.functions import col, sum as spark_sum
import sys

# ------------------------------
# Replace these with your actual values
# ------------------------------
INPUT_PATH = "s3://your-source-bucket/path/to/input.csv"
CLEANED_OUTPUT_PATH = "s3://your-target-bucket/cleaned_data/"
AGGREGATED_OUTPUT_PATH = "s3://your-target-bucket/aggregated_data/"

def main():
    print("Starting Spark job...")

    schema = StructType([
        StructField("transaction_id", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("store", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("product_category", StringType(), True),
        StructField("quantity", IntegerType(), True),
        StructField("price", DoubleType(), True),
    ])

    spark = SparkSession.builder.appName("CleanAndAggregateSales").getOrCreate()

    try:
        print(f"Reading data from: {INPUT_PATH}")
        df = spark.read.csv(INPUT_PATH, header=True, schema=schema)

        expected_cols = {"transaction_id", "timestamp", "store", "customer_id", "product_category", "quantity", "price"}
        actual_cols = set(df.columns)
        missing_cols = expected_cols - actual_cols
        if missing_cols:
            raise ValueError(f"Missing expected columns: {missing_cols}")

        print("Dropping duplicate transactions...")
        df_deduped = df.dropDuplicates(["transaction_id", "timestamp", "store", "customer_id"])

        print("Filtering invalid rows (quantity <= 0 or price <= 0)...")
        df_valid = df_deduped.filter(
            (col("quantity") > 0) & 
            (col("price") > 0)
        )

        print("Calculating sales amount...")
        df_with_sales = df_valid.withColumn("sales_amount", col("quantity") * col("price"))

        print("Aggregating total sales by store and category...")
        df_aggregated = df_with_sales.groupBy("store", "product_category") \
            .agg(spark_sum("sales_amount").alias("total_sales"))

        print(f"Writing cleaned data to: {CLEANED_OUTPUT_PATH}")
        df_valid.write.mode("overwrite").option("header", "true") \
            .partitionBy("store") \
            .csv(CLEANED_OUTPUT_PATH)

        print(f"Writing aggregated data to: {AGGREGATED_OUTPUT_PATH}")
        df_aggregated.write.mode("overwrite").option("header", "true") \
            .csv(AGGREGATED_OUTPUT_PATH)

        print("Job completed successfully.")

    except Exception as e:
        print(f"Spark job failed: {e}", file=sys.stderr)
        raise
    finally:
        spark.stop()
        print("Spark session stopped.")

if __name__ == "__main__":
    main()
