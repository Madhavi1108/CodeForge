import json
import logging
from confluent_kafka import Producer
from core.config import settings

logger = logging.getLogger(__name__)

class ConfluentKafkaProducer:
    def __init__(self):
        conf = {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'client.id': 'codeforge-api-producer'
        }
        self.producer = Producer(conf)

    def delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def produce(self, topic: str, key: str, value: dict):
        self.producer.produce(
            topic=topic,
            key=key,
            value=json.dumps(value).encode('utf-8'),
            callback=self.delivery_report
        )
        self.producer.flush()

    def flush(self):
        self.producer.flush()

kafka_producer = ConfluentKafkaProducer()
