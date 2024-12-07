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

schema = StructType([StructField("message", StringType(), True)])

packages = [
    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3",
    "org.apache.spark:spark-avro_2.12:3.5.3",
]

spark =  SparkSession\
    .builder\
    .appName("FinanceStream")\
    .master("spark://localhost:7077")\
    .config("spark.jars.packages", ",".join(packages))\
    .getOrCreate()

kafka_stream = spark\
    .readStream\
    .format("kafka")\
    .option("kafka.bootstrap.servers", f"{KAFKA_SERVER}:{KAFKA_PORT}")\
    .option("subscribe", KAFKA_TOPIC_NAME)\
    .option("startingOffsets", "earliest")\
    .load()


# Doesnt work yet
avro_stream = kafka_stream.selectExpr("CAST(value AS BINARY)")\
    .select(from_avro("value", schema).alias("data"))\
    .select("data.message")


print(avro_stream)


