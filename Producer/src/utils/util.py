import avro.io
import finnhub
from io import BytesIO


def create_client(token: str):
    """
    Connect to Finnhub
    """
    return finnhub.Client(api_key=token)


def check_symbol_exists(exchange: str, ticker: str, finnhub_client):
    """
    Returns True if symbol exists on Finnhub's Crypto exchance
    """
    for crypto in finnhub_client.crypto_symbols(exchange):
        if crypto["symbol"] == f"{exchange}:{ticker}":
            return True

    return False


def avro_encode(data, schema):
    """
    Encode message as avro format
    """
    writer = avro.io.DatumWriter(schema)
    bytes_writer = BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer.write(data, encoder)
    return bytes_writer.getvalue()
