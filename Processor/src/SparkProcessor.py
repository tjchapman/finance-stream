import uuid
import logging
from os import getenv
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.avro.functions import from_avro
from pyspark.sql.types import StructType, StructField, StringType
from pyspark.sql.functions import explode, col, current_timestamp, expr, from_unixtime, window, avg


logger = logging.getLogger(__name__)
FORMAT = "%(levelname)s\t%(asctime)s\t%(funcName)s\t%(message)s\t"

logging.basicConfig(level=logging.INFO, format=FORMAT)

load_dotenv()

# TODO: put me in a class please

KAFKA_SERVER = getenv("KAFKA_SERVER")
KAFKA_PORT = getenv("KAFKA_PORT")
KAFKA_TOPIC_NAME = getenv("KAFKA_TOPIC_NAME")

CASSANDRA_USERNAME = getenv("CASSANDRA_USERNAME")
CASSANDRA_PASSWORD = getenv("CASSANDRA_PASSWORD")
CASSANDRA_HOST = getenv("CASSANDRA_HOST")

with open("Producer/src/schema/prices.avsc", "r") as schema_file:
    schema = schema_file.read()

packages = [
    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3",
    "org.apache.spark:spark-avro_2.12:3.5.3",
    "com.datastax.spark:spark-cassandra-connector_2.12:3.5.1"
]

spark =  SparkSession\
    .builder\
    .appName("FinanceStream")\
    .config("spark.jars.packages", ",".join(packages))\
    .config('spark.cassandra.connection.host', CASSANDRA_HOST)\
    .config('spark.cassandra.auth.usernane', CASSANDRA_USERNAME)\
    .config('spark.cassandra.auth.password', CASSANDRA_PASSWORD)\
    .getOrCreate()

logger.info('Spark connection created successfully.')


# Stream from Kafka into Spark
kafka_stream = spark\
    .readStream\
    .format("kafka")\
    .option("kafka.bootstrap.servers", f"{KAFKA_SERVER}:{KAFKA_PORT}")\
    .option("subscribe", KAFKA_TOPIC_NAME)\
    .option("startingOffsets", "earliest")\
    .load()
logger.info("Kafka dataframe created successfully")

# Parse Avro Binary through Schema
avro_stream = kafka_stream\
            .select(from_avro("value", schema).alias("data"))
# avro_stream.printSchema()

# Explode/Flatten Avro Nested Format
flattend_stream = avro_stream.select(
    col("data.type").alias("type"),
    explode(col("data.data")).alias('exploded_data')
).select(
    expr("uuid()").alias("id"),
    col("type"),
    col("exploded_data.c").alias("conditions"),
    col("exploded_data.p").alias("price"),
    col("exploded_data.s").alias("symbol"), # maybe seperate out EXCHANGE:SYMBOL
    from_unixtime(col("exploded_data.t")/1000).alias("timestamp"),
    col("exploded_data.v").alias("volume"),
    current_timestamp().alias("proc_time"),
)

aggregated_stream = flattend_stream.groupBy(
    window(col("timestamp"), "10 seconds"),
    col("symbol")
).agg(
    avg("price").alias("average_price"),
    avg("volume").alias("average_volume")
).select(
    col("window.start").alias("start_time"), 
    col("window.end").alias("end_time"),  
    col("symbol"),
    col("average_price"),
    col("average_volume")
)



# Write stream to console for testing TODO: remove this
# flattend_stream.writeStream \
#     .format("console") \
#     .outputMode("append") \
#     .start()\
#     .awaitTermination()

aggregated_stream.writeStream \
    .format("console") \
    .outputMode("update") \
    .option("truncate", "false")\
    .start()\
    .awaitTermination()
