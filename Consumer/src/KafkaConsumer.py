import json
import logging
from os import getenv
from dotenv import load_dotenv
from kafka import KafkaConsumer

logger = logging.getLogger(__name__)
FORMAT = "%(levelname)s\t%(asctime)s\t%(funcName)s\t%(message)s\t"

logging.basicConfig(level=logging.INFO, format=FORMAT)

load_dotenv()

KAFKA_SERVER = getenv("KAFKA_SERVER")
KAFKA_PORT = getenv("KAFKA_PORT")
KAFKA_TOPIC_NAME = getenv("KAFKA_TOPIC_NAME")

consumer = KafkaConsumer(
    KAFKA_TOPIC_NAME, bootstrap_servers=f"{KAFKA_SERVER}:{KAFKA_PORT}"
)

for message in consumer:
    print(json.loads(message.value))
