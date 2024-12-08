import logging
from os import getenv
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.avro.functions import from_avro
from pyspark.sql.types import StructType, StructField, StringType

logger = logging.getLogger(__name__)
FORMAT = "%(levelname)s\t%(asctime)s\t%(funcName)s\t%(message)s\t"

logging.basicConfig(level=logging.INFO, format=FORMAT)

load_dotenv()

KAFKA_SERVER = getenv("KAFKA_SERVER")
KAFKA_PORT = getenv("KAFKA_PORT")
KAFKA_TOPIC_NAME = getenv("KAFKA_TOPIC_NAME")

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
    .getOrCreate()

logger.info('Spark connection created successfully.')

    #  .config('spark.cassandra.connection.host', 'localhost')\

    # .config("spark.executor.memory", "512m")\
    # .config("spark.executor.cores", "1")\
    # .config("spark.driver.cores", "1")\


kafka_stream = spark\
    .readStream\
    .format("kafka")\
    .option("kafka.bootstrap.servers", f"{KAFKA_SERVER}:{KAFKA_PORT}")\
    .option("subscribe", KAFKA_TOPIC_NAME)\
    .option("startingOffsets", "earliest")\
    .load()
logger.info("Kafka dataframe created successfully")

avro_stream = kafka_stream\
            .select(from_avro("value", schema).alias("data"))
avro_stream.printSchema()

# Write stream to console for testing
query = avro_stream.writeStream \
    .format("console") \
    .outputMode("append") \
    .start()

query.awaitTermination()
