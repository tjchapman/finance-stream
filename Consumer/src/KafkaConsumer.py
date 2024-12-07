import avro
import logging
from os import getenv
from dotenv import load_dotenv
from kafka import KafkaConsumer
from utils.util import avro_decode

logger = logging.getLogger(__name__)
FORMAT = "%(levelname)s\t%(asctime)s\t%(funcName)s\t%(message)s\t"

logging.basicConfig(level=logging.INFO, format=FORMAT)

load_dotenv()


class Consumer:
    """
    Class that consumes Kafka messages from a topic and deserializes them
    """

    def __init__(self):
        self.KAFKA_SERVER = getenv("KAFKA_SERVER")
        self.KAFKA_PORT = getenv("KAFKA_PORT")
        self.KAFKA_TOPIC_NAME = getenv("KAFKA_TOPIC_NAME")
        self.schema = avro.schema.Parse(
            open("Producer/src/schema/prices.avsc", "r").read()
        )

    def consume(self):
        self.consumer = KafkaConsumer(
            self.KAFKA_TOPIC_NAME,
            bootstrap_servers=f"{self.KAFKA_SERVER}:{self.KAFKA_PORT}",
        )

        for message in self.consumer:
            decoded = avro_decode(message_value=message.value, schema=self.schema)
            logger.info(decoded)
            yield decoded


if __name__ == "__main__":
    Consumer().consume()
