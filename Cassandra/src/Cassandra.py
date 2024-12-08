import logging
from os import getenv
from dotenv import load_dotenv
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

logger = logging.getLogger(__name__)
FORMAT = "%(levelname)s\t%(asctime)s\t%(funcName)s\t%(message)s\t"

logging.basicConfig(level=logging.INFO, format=FORMAT)

load_dotenv()


class Cassandra:
    """
    Class that setups up required Cassandra Keyspace and Tables
    """

    def __init__(self):
        self.CASSANDRA_USERNAME = getenv("CASSANDRA_USERNAME")
        self.CASSANDRA_PASSWORD = getenv("CASSANDRA_PASSWORD")
        self.CASSANDRA_HOST = getenv("CASSANDRA_HOST")
        self.keyspace = "crypto"

    def connect_to_cassandra(self):
        try:
            auth_provider = PlainTextAuthProvider(
                username=self.CASSANDRA_USERNAME, password=self.CASSANDRA_PASSWORD
            )
            cluster = Cluster([self.CASSANDRA_HOST], auth_provider=auth_provider)
            self.session = cluster.connect()

            logger.info("Cassandra connection created successfully.")

        except Exception as e:
            logger.error(f"Failed to connect to Cassandra: {e}")
            raise

        return

    def create_and_set_keyspace(self):
        try:
            self.session.execute(f"""
                        CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
                        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': '1'}};
                        """)
            logger.info("Cassandra Keyspace created successfully.")
            self.session.set_keyspace(self.keyspace)
            logger.info(f"Now using keyspace: {self.keyspace}")

        except Exception as e:
            logger.error(f"Failed to create or set keyspace: {e}")
            raise

        return

    def create_raw_cassandra_table(self):
        try:
            self.session.execute("""
            CREATE TABLE IF NOT EXISTS crypto_prices (
                id uuid,
                type text,
                conditions text,
                price double,
                symbol text,
                crypto_timestamp timestamp,
                volume double,
                proc_time timestamp,
                PRIMARY KEY((symbol),crypto_timestamp))
            WITH CLUSTERING ORDER BY (crypto_timestamp DESC);
            """)

            self.session.execute("""
            CREATE INDEX IF NOT EXISTS ON crypto_prices (id);
            """)

            logger.info("Raw table successfully created")

        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            raise

        return

    def create_agg_cassandra_table(self):
        try:
            self.session.execute("""
            CREATE TABLE IF NOT EXISTS crypto_prices_agg (
                id uuid,
                start_time timestamp,
                end_time timestamp,
                symbol text,
                average_price double,
                average_volume double,
                proc_time timestamp,
                PRIMARY KEY((id),proc_time))
            WITH CLUSTERING ORDER BY 
            (proc_time DESC);
            """)

            self.session.execute("""
            CREATE INDEX IF NOT EXISTS ON crypto_prices_agg (symbol);
            """)

            logger.info("Aggregated table successfully created")

        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            raise

        return

    def drop_tables(self):
        tables = ["crypto_prices", "crypto_prices_agg"]
        for table in tables:
            self.session.execute(f"DROP TABLE IF EXISTS {table}")
            logger.info(f"Dropped table: {table}")

        return

    def setup(self, clean_out=False):
        self.connect_to_cassandra()
        self.create_and_set_keyspace()
        if clean_out:
            self.drop_tables()

        self.create_raw_cassandra_table()
        self.create_agg_cassandra_table()

        return


if __name__ == "__main__":
    Cassandra().setup()
