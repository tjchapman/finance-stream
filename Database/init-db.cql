CREATE KEYSPACE IF NOT EXISTS crypto
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'};

USE crypto;

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

CREATE TABLE IF NOT EXISTS crypto_prices_agg (
                id uuid,
                start_time timestamp,
                end_time timestamp,
                symbol text,
                average_price double,
                average_volume double,
                proc_time timestamp,
                PRIMARY KEY((id),proc_time))
WITH CLUSTERING ORDER BY (proc_time DESC);

CREATE INDEX IF NOT EXISTS ON crypto_prices (id);
CREATE INDEX IF NOT EXISTS ON crypto_prices_agg (symbol);
