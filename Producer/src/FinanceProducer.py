import json
import logging
import websocket
import avro.schema
from os import getenv
from ast import literal_eval
from dotenv import load_dotenv
from kafka import KafkaProducer
from utils.util import create_client, check_symbol_exists, avro_encode


logger = logging.getLogger(__name__)
FORMAT = "%(levelname)s\t%(asctime)s\t%(funcName)s\t%(message)s\t"

logging.basicConfig(level=logging.INFO, format=FORMAT)

load_dotenv()


class FinanceProducer:
    """
    Class that pulls tickers from Finnhub websocket and publishes messages to Kafka.
    """

    def __init__(self):
        self.FINNHUB_KEY = getenv("FINNHUB_API_KEY")
        self.TICKERS = literal_eval(getenv("FINNHUB_TICKERS"))
        self.KAFKA_SERVER = getenv("KAFKA_SERVER")
        self.KAFKA_PORT = getenv("KAFKA_PORT")
        self.KAFKA_TOPIC_NAME = getenv("KAFKA_TOPIC_NAME")

        self.finnhub_client = create_client(token=self.FINNHUB_KEY)
        self.kafka = KafkaProducer(
            bootstrap_servers=f"{self.KAFKA_SERVER}:{self.KAFKA_PORT}"
        )

        self.schema = avro.schema.Parse(
            open("Producer/src/schema/prices.avsc", "r").read()
        )

    def on_message(self, ws, message):
        message = json.loads(message)
        logger.info(f"Encoding and sending record to Kafka: {message}")
        encoded_message = avro_encode(
            {"data": message["data"], "type": message["type"]}, self.schema
        )
        encoded_message = json.dumps(message).encode("utf-8")
        logger.info(f"Sending record to Kafka: {encoded_message}")
        self.kafka.send(self.KAFKA_TOPIC_NAME, encoded_message)
        return

    def on_error(self, ws, error):
        logger.info(error)
        return

    def on_close(self, ws):
        logger.info("### closed ###")
        return

    def on_open(self, ws, exchange: str = "BINANCE"):
        for ticker in self.TICKERS:
            if check_symbol_exists(
                exchange=exchange, ticker=ticker, finnhub_client=self.finnhub_client
            ):
                ws.send(f'{{"type":"subscribe","symbol":"{exchange}:{ticker}"}}')
                logger.info(f"Subscription to {ticker} successful")
            else:
                logger.error(f"Unable to subscribe to {ticker} - does not exist")
        return

    def produce(self):
        logger.info(f"Pulling info for: {self.TICKERS}")
        FINNHUB_URL = f"wss://ws.finnhub.io?token={self.FINNHUB_KEY}"
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            FINNHUB_URL,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.ws.on_open = self.on_open
        self.ws.run_forever()
        return


if __name__ == "__main__":
    FinanceProducer().produce()
