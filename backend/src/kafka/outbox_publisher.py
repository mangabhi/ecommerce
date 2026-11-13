
import json
import os
import time

from confluent_kafka import Producer
from sqlalchemy import select

from src.kafka.models import OutboxEvent
from src.utils.db import LocalSession


class OutboxPublisher:

    def __init__(self):
        bootstrap_servers = os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092",
        )

        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "acks": "all",
            "enable.idempotence": True,
            "retries": 2147483647,
            "delivery.timeout.ms": 120000,
        })

        self.batch_size = 10
        self.poll_interval = 5

    def publish_event(self, event):
        delivery_result = {
            "success": False,
            "error": None,
        }

        def delivery_report(err, msg):
            if err is not None:
                delivery_result["error"] = str(err)
            else:
                delivery_result["success"] = True

                print(
                    f"Event delivered: {event.event_id} | "
                    f"Topic: {msg.topic()} | "
                    f"Partition: {msg.partition()} | "
                    f"Offset: {msg.offset()}"
                )

        try:
            self.producer.produce(
                topic=event.topic,
                key=str(event.payload["order_id"]),
                value=json.dumps(event.payload),
                callback=delivery_report,
            )

            # Wait for Kafka delivery confirmation.
            remaining = self.producer.flush(timeout=10)

            if remaining > 0:
                raise TimeoutError(
                    "Kafka delivery timed out"
                )

            if not delivery_result["success"]:
                raise RuntimeError(
                    delivery_result["error"]
                    or "Kafka delivery failed"
                )

            return True

        except Exception as error:
            print(
                f"Failed to publish event "
                f"{event.event_id}: {error}"
            )
            return False

    def process_pending_events(self):

        db = LocalSession()

        try:
            events = (
                db.execute(
                    select(OutboxEvent)
                    .where(OutboxEvent.published.is_(False))
                    .order_by(OutboxEvent.id)
                    .limit(self.batch_size)
                    .with_for_update(skip_locked=True)
                )
                .scalars()
                .all()
            )

            if not events:
                return 0

            published_count = 0

            for event in events:

                success = self.publish_event(event)

                if success:
                    event.published = True
                    published_count += 1

            if published_count > 0:
                db.commit()
                print(
                    f"Published {published_count} "
                    f"outbox event(s)"
                )
            else:
                db.rollback()

            return published_count

        except Exception as error:
            db.rollback()
            print(f"Outbox processing error: {error}")
            return 0

        finally:
            db.close()

    def run(self):

        print("Outbox Publisher started")

        try:
            while True:
                self.process_pending_events()
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            print("Outbox Publisher stopped")

        finally:
            self.producer.flush(timeout=10)


if __name__ == "__main__":

    publisher = OutboxPublisher()
    publisher.run()
