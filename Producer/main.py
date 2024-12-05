import logging
import websocket
from os import getenv
from typing import List
from ast import literal_eval
from dotenv import load_dotenv
from src.utils.util import create_client

logger = logging.getLogger(__name__)
FORMAT= "%(levelname)s\t%(asctime)s\t%(funcName)s\t%(message)s\t"

logging.basicConfig(level=logging.INFO,
                     format=FORMAT)

load_dotenv()

FINNHUB_KEY = getenv('FINNHUB_API_KEY')
tickers = literal_eval(getenv('FINNHUB_TICKERS'))

finnhub_client = create_client(token=FINNHUB_KEY)
logger.info(finnhub_client)

'''
just trying the webhook for now
'''

def on_message(ws, message):
    logger.info(message)

def on_error(ws, error):
    logger.info(error)

def on_close(ws):
    logger.info("### closed ###")

def on_open(ws, tickers: List[str]=tickers, exchange:str='BINANCE'):
    for ticker in tickers:
        ws.send(f'{{"type":"subscribe","symbol":"{exchange}:{ticker}"}}')
        logger.info(f'Subscription to {ticker} successful')
    logger.info(f'Subscription succeeded')


def main():
    logger.info(f'Pulling tickers for: {tickers}')
    FINNHUB_URL = f'wss://ws.finnhub.io?token={FINNHUB_KEY}'
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(FINNHUB_URL, 
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()

if __name__ == "__main__":
    main()


    
