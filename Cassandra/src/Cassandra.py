import logging
from os import getenv
from dotenv import load_dotenv
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

logger = logging.getLogger(__name__)
FORMAT = "%(levelname)s\t%(asctime)s\t%(funcName)s\t%(message)s\t"

logging.basicConfig(level=logging.INFO, format=FORMAT)

load_dotenv()

# TODO: put me in a class please

CASSANDRA_USERNAME = getenv("CASSANDRA_USERNAME")
CASSANDRA_PASSWORD = getenv("CASSANDRA_PASSWORD")
CASSANDRA_HOST = getenv("CASSANDRA_HOST")


def connect_to_cassandra(username: str, password: str, host: str):
    try:
        auth_provider = PlainTextAuthProvider(username=username, password=password)
        cluster = Cluster([host], auth_provider=auth_provider)
        session = cluster.connect()
        logger.info("Cassandra connection created successfully.")

    except Exception as e:
        logger.error(f"Failed to connect to Cassandra: {e}")
        raise

    return session


def create_and_set_keyspace(keyspace: str, session):
    try:
        session.execute(f"""
                    CREATE KEYSPACE IF NOT EXISTS {keyspace}
                    WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': '1'}};
                    """)
        logger.info("Cassandra Keyspace created successfully.")
        session.set_keyspace(keyspace)
        logger.info(f"Now using keyspace: {keyspace}")

    except Exception as e:
        logger.error(f"Failed to create or set keyspace: {e}")
        raise

    return


def create_cassandra_tables(session):
    try:
        session.execute("""
        CREATE TABLE IF NOT EXISTS crypto_prices (
            uuid uuid,
            symbol text,
            trade_conditions text,
            price double,
            volume double,
            trade_timestamp timestamp,
            ingest_timestamp timestamp,
            PRIMARY KEY((symbol),trade_timestamp))
        WITH CLUSTERING ORDER BY (trade_timestamp DESC);
        """)

        session.execute("""
        CREATE INDEX IF NOT EXISTS ON crypto_prices (uuid);
        """)

    except Exception as e:
        logger.error(f"Failed to create table: {e}")
        raise

    return


session = connect_to_cassandra(
    username=CASSANDRA_USERNAME, password=CASSANDRA_PASSWORD, host=CASSANDRA_HOST
)

create_and_set_keyspace(keyspace="crypto", session=session)
create_cassandra_tables(session=session)
