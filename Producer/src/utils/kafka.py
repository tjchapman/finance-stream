from kafka import KafkaProducer


def kafka_producer(kafka_server):
    """
    Creates Kafka connection
    """
    return KafkaProducer(bootstrap_servers=kafka_server)
