from pyspark.sql import SparkSession
from pyspark.sql.functions import col, unbase64
from pyspark.sql.types import StringType

def main():
    # Khởi tạo SparkSession với master là local[*]
    spark = SparkSession.builder \
        .appName("KafkaSparkBase64Decode") \
        .master("local[*]") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Cấu hình Kafka: thay đổi kafka_bootstrap_servers nếu cần
    kafka_bootstrap_servers = "kafk-1:9094,kafk-2:9094,kafk-3:9094"
    topic = "esp32_data"  # Thay thế nếu cần

    # Đọc dữ liệu stream từ Kafka, key và value được đọc ở dạng binary
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", topic) \
        .option("startingOffsets", "latest") \
        .load()

    # Giữ lại cột "value" và chuyển đổi key sang string
    kafka_df = kafka_df.selectExpr("CAST(key AS STRING) as key", "CAST(value AS STRING) as value", "timestamp")

    # Sử dụng hàm unbase64 để giải mã cột "value" và cast kết quả sang string
    decoded_df = kafka_df.withColumn("decoded_value", unbase64(col("value")).cast("string")) \
                         .select("key", "decoded_value", "timestamp")

    # Ghi kết quả ra console mỗi 10 giây
    query = decoded_df.writeStream \
        .format("console") \
        .option("truncate", "false") \
        .trigger(processingTime="10 seconds") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
