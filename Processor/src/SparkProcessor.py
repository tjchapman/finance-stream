import uuid
import logging
from os import getenv
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.avro.functions import from_avro
from pyspark.sql.types import StructType, StructField, StringType
from pyspark.sql.functions import explode, col, current_timestamp, expr, from_unixtime, window, avg, to_timestamp


logger = logging.getLogger(__name__)
FORMAT = "%(levelname)s\t%(asctime)s\t%(funcName)s\t%(message)s\t"

logging.basicConfig(level=logging.INFO, format=FORMAT)

load_dotenv()

class SparkProcessor:
    """
    Class that runs Spark Processing on our data and outputs the streams to a Cassandra DB.
    """
    def __init__(self):
        self.KAFKA_SERVER = getenv("KAFKA_SERVER")
        self.KAFKA_PORT = getenv("KAFKA_PORT")
        self.KAFKA_TOPIC_NAME = getenv("KAFKA_TOPIC_NAME")

        self.CASSANDRA_USERNAME = getenv("CASSANDRA_USERNAME")
        self.CASSANDRA_PASSWORD = getenv("CASSANDRA_PASSWORD")
        self.CASSANDRA_HOST = getenv("CASSANDRA_HOST")

        with open("Producer/src/schema/prices.avsc", "r") as schema_file:
            self.schema = schema_file.read()

        self.packages = [
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3",
            "org.apache.spark:spark-avro_2.12:3.5.3",
            "com.datastax.spark:spark-cassandra-connector_2.12:3.5.1"
        ]

    def create_spark_session(self):
        self.spark =  SparkSession\
            .builder\
            .appName("FinanceStream")\
            .config("spark.jars.packages", ",".join(self.packages))\
            .config('spark.cassandra.connection.host', self.CASSANDRA_HOST)\
            .config('spark.cassandra.auth.username', self.CASSANDRA_USERNAME)\
            .config('spark.cassandra.auth.password', self.CASSANDRA_PASSWORD)\
            .getOrCreate()
        self.spark.sparkContext.setLogLevel("ERROR")
        logger.info('Spark connection created successfully.')
        return 

    def connect_spark_to_kafka(self): 
        """
        Stream from Kafka into Spark
        """
        self.kafka_stream = self.spark\
            .readStream\
            .format("kafka")\
            .option("kafka.bootstrap.servers", f"{self.KAFKA_SERVER}:{self.KAFKA_PORT}")\
            .option("subscribe", self.KAFKA_TOPIC_NAME)\
            .option("startingOffsets", "earliest")\
            .load()
        logger.info("Kafka dataframe created successfully")
        return 

    def parse_avro_schema(self):
        self.avro_stream = self.kafka_stream\
                    .select(from_avro("value", self.schema).alias("data"))
        # avro_stream.printSchema()
        return

    def flatten_data(self):
        """
        Explode/Flatten Avro Nested Format
        """
        self.flattend_stream = self.avro_stream.select(
            col("data.type").alias("type"),
            explode(col("data.data")).alias('exploded_data')
        ).select(
            expr("uuid()").alias("id"),
            col("type"),
            col("exploded_data.c").alias("conditions"),
            col("exploded_data.p").alias("price"),
            col("exploded_data.s").alias("symbol"), # maybe seperate out EXCHANGE:SYMBOL
            from_unixtime(col("exploded_data.t")/1000).alias("crypto_timestamp"),
            col("exploded_data.v").alias("volume"),
            current_timestamp().alias("proc_time")
        )
        return

    def apply_watermark(self):
        """
        Apply watermark to handle late data
        """
        self.flattend_stream_with_watermark = self.flattend_stream \
            .withColumn("crypto_timestamp", to_timestamp(col("crypto_timestamp"))) \
            .withWatermark("crypto_timestamp", "10 seconds") 
        return

    def aggregate_stream(self):
        """
        Aggregated stream from watermarked flat
        """
        self.aggregated_stream = self.flattend_stream_with_watermark.groupBy(
            window(col("crypto_timestamp"), "10 seconds"),
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

        # Add uuid and process time to aggregated stream
        self.final_stream = self.aggregated_stream.select(
            expr("uuid()").alias("id"),
            col("start_time"), 
            col("end_time"),  
            col("symbol"),
            col("average_price"),
            col("average_volume"),
            current_timestamp().alias("proc_time")
        )
        return

    def write_data_to_cassandra(self):
        logger.info('Writing raw & aggregated data to Cassandra...')
        # Insert Raw Data into Cassandra
        self.flattend_stream_query = self.flattend_stream.writeStream \
            .format("org.apache.spark.sql.cassandra") \
            .options(table="crypto_prices", keyspace="crypto") \
            .option("checkpointLocation", "/tmp/checkpoints/crypto_prices") \
            .start()

        # Insert Aggregated Data into Cassandra
        self.final_stream_query = self.final_stream.writeStream \
            .format("org.apache.spark.sql.cassandra") \
            .options(table="crypto_prices_agg", keyspace="crypto") \
            .option("checkpointLocation", "/tmp/checkpoints/crypto_prices_agg") \
            .start()

        self.flattend_stream_query.awaitTermination()
        self.final_stream_query.awaitTermination()
        return

    def write_to_console(self):
        """
        Write stream to console for testing
        """ 
        query1 = self.flattend_stream.writeStream \
            .format("console") \
            .outputMode("append") \
            .start()
    
        query2 = self.final_stream.writeStream \
            .format("console") \
            .outputMode("update") \
            .option("truncate", "false")\
            .start()

        query1.awaitTermination()
        query2.awaitTermination()
        return

    def process(self, write_to_db:bool=True):
        self.create_spark_session()
        self.connect_spark_to_kafka()
        self.parse_avro_schema()
        self.flatten_data()
        self.apply_watermark()
        self.aggregate_stream()
        if write_to_db:
            self.write_data_to_cassandra()
        else:
            self.write_to_console()


if __name__ == "__main__":
    SparkProcessor().process()
