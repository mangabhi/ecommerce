
import json
import os
from confluent_kafka import Producer


class KafkaProducerService:
    def __init__(self):
        bootstrap_servers = os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092"
        )

        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "acks": "all",
            "enable.idempotence": True,
            "retries": 2147483647,
            "delivery.timeout.ms": 120000,
        })

    def delivery_report(self, err, msg):
        if err is not None:
            print(f"Message delivery failed: {err}")
        else:
            print(
                f"Message Delivered to {msg.topic()}"
                f"[Partition {msg.partition()}]"
                f"at offset {msg.offset()}"
            )

    def publish(self, topic, event):
        self.producer.produce(
            topic=topic,
            value=json.dumps(event),
            callback=self.delivery_report
        )
        self.producer.poll(0)

    def flush(self):
        self.producer.flush()


kafka_producer = KafkaProducerService()
