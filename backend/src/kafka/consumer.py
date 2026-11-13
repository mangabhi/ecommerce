
import json
import os
import time
import signal

from confluent_kafka import Consumer, Producer, TopicPartition
from sqlalchemy.exc import IntegrityError, OperationalError

from src.kafka.models import ProcessedEvent
from src.notifications.models import Notification
from src.utils.db import LocalSession

# Register SQLAlchemy models and relationships.
from src.auth.models import AuthUser
from src.user.models import UserProfile, Address


# Custom exception classes
class PermanentEventError(Exception):
    """Raised when an event cannot succeed by retrying."""


class TransientProcessingError(Exception):
    """Raised when an event may succeed after retrying."""


# Retry configuration
MAX_RETRIES = 3
BASE_RETRY_DELAY = 1
MAX_RETRY_DELAY = 10


def get_retry_delay(attempt: int) -> int:
    """Calculate exponential backoff delay."""
    delay = BASE_RETRY_DELAY * (2 ** (attempt - 1))
    return min(delay, MAX_RETRY_DELAY)


class KafkaConsumerService:

    def __init__(self, group_id: str):
        bootstrap_servers = os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092",
        )

        self.group_id = group_id

        self.consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "enable.auto.offset.store": False,
        })

        # Producer for Dead Letter Topic
        self.dlt_producer = Producer({
            "bootstrap.servers": bootstrap_servers,
        })
        self.running=True

    def process_event(self, event: dict):
        """Validate and process an OrderCreated event."""

        # 1. Validate event structure
        if not isinstance(event, dict):
            raise PermanentEventError(
                "Event payload must be a JSON object"
            )

        required_fields = [
            "event_id",
            "event_type",
            "order_id",
            "user_id",
        ]

        missing_fields = [
            field for field in required_fields
            if field not in event
        ]

        if missing_fields:
            raise PermanentEventError(
                f"Missing required fields: {missing_fields}"
            )

        # 2. Validate event ID
        event_id = event["event_id"]

        if not isinstance(event_id, str) or not event_id.strip():
            raise PermanentEventError(
                "event_id must be a non-empty string"
            )

        # 3. Validate event type
        event_type = event["event_type"]

        if event_type != "OrderCreated":
            raise PermanentEventError(
                f"Unsupported event type: {event_type}"
            )

        # 4. Validate order_id and user_id
        try:
            order_id = int(event["order_id"])
            user_id = int(event["user_id"])

        except (ValueError, TypeError):
            raise PermanentEventError(
                "order_id and user_id must be valid integers"
            )

        if order_id <= 0 or user_id <= 0:
            raise PermanentEventError(
                "order_id and user_id must be positive"
            )

        # 5. Process event in PostgreSQL
        db = LocalSession()

        try:
            # Reserve event ID to prevent duplicate processing.
            db.add(ProcessedEvent(event_id=event_id))
            db.flush()

            notification = Notification(
                user_id=user_id,
                title="Order placed successfully",
                message=(
                    f"Your order #{order_id} "
                    "has been placed successfully."
                ),
            )

            db.add(notification)

            # Commit notification and processed event together.
            db.commit()

            print(
                f"Processed OrderCreated | "
                f"event_id={event_id} | "
                f"order_id={order_id}",
                flush=True,
            )

        except IntegrityError:
            db.rollback()

            existing = (
                db.query(ProcessedEvent)
                .filter(ProcessedEvent.event_id == event_id)
                .first()
            )

            if existing is None:
                raise

            print(
                f"Duplicate event skipped: {event_id}",
                flush=True,
            )

        except OperationalError as error:
            db.rollback()

            print(
                f"Database operational error: {error}",
                flush=True,
            )

            raise TransientProcessingError(
                "Temporary database failure"
            ) from error

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def process_with_retries(self, msg) -> tuple[bool, str | None]:
        """Process a Kafka message with intelligent error classification."""

        last_error = None

        # Step 1: Decode JSON before retrying.
        try:
            event = json.loads(
                (msg.value() or b"").decode("utf-8")
            )

        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            print(
                f"Permanent message error: {error}",
                flush=True,
            )
            return False, f"Invalid JSON message: {error}"

        # Step 2: Process with bounded retries.
        for attempt in range(1, MAX_RETRIES + 1):

            try:
                print(
                    f"Processing attempt {attempt}/{MAX_RETRIES}",
                    flush=True,
                )

                self.process_event(event)

                return True, None

            except PermanentEventError as error:
                print(
                    f"Permanent event error: {error}",
                    flush=True,
                )

                return False, str(error)

            except TransientProcessingError as error:
                last_error = str(error)

                print(
                    f"Transient error on attempt "
                    f"{attempt}/{MAX_RETRIES}: {error}",
                    flush=True,
                )

                if attempt < MAX_RETRIES:
                    delay = get_retry_delay(attempt)

                    print(
                        f"Retrying in {delay} seconds...",
                        flush=True,
                    )

                    time.sleep(delay)

            except Exception as error:
                last_error = str(error)

                print(
                    f"Unexpected processing error: {error}",
                    flush=True,
                )

                return False, last_error

        # Step 3: Maximum retries exhausted.
        print(
            f"Maximum retries exhausted | "
            f"Topic: {msg.topic()} | "
            f"Partition: {msg.partition()} | "
            f"Offset: {msg.offset()}",
            flush=True,
        )

        return False, last_error

    def publish_to_dlt(self, msg, error: str) -> bool:
        """Publish a failed message to the Dead Letter Topic."""

        dlt_topic = f"{msg.topic()}.DLT"

        dlt_event = {
            "original_topic": msg.topic(),
            "original_partition": msg.partition(),
            "original_offset": msg.offset(),
            "error": error,
            "original_message": (msg.value() or b"").decode(
                "utf-8",
                errors="replace",
            ),
            "failed_at": time.time(),
        }

        delivery_result = {
            "success": False,
            "error": None,
        }

        def delivery_report(err, kafka_msg):
            if err is not None:
                delivery_result["error"] = str(err)
            else:
                delivery_result["success"] = True

        try:
            original_key = msg.key()

            self.dlt_producer.produce(
                topic=dlt_topic,
                key=(
                    original_key.decode("utf-8", errors="replace")
                    if original_key is not None
                    else None
                ),
                value=json.dumps(dlt_event),
                callback=delivery_report,
            )

            remaining = self.dlt_producer.flush(timeout=10)

            if remaining > 0:
                raise TimeoutError("DLT delivery timed out")

            if not delivery_result["success"]:
                raise RuntimeError(
                    delivery_result["error"]
                    or "DLT delivery failed"
                )

            print(
                f"Message published to DLT: {dlt_topic} | "
                f"Original offset: {msg.offset()}",
                flush=True,
            )

            return True

        except Exception as error:
            print(
                f"DLT publishing failed: {error}",
                flush=True,
            )
            return False

    def commit_offset(self, msg):
        """Commit the next Kafka offset after successful processing."""

        next_offset = msg.offset() + 1

        try:
            self.consumer.commit(
                offsets=[
                    TopicPartition(
                        msg.topic(),
                        msg.partition(),
                        next_offset,
                    )
                ],
                asynchronous=False,
            )

            print(
                f"Offset committed: "
                f"{msg.topic()} [{msg.partition()}] "
                f"next offset {next_offset}",
                flush=True,
            )

            return True

        except Exception as error:
            print(
                f"Offset commit failed: {error}",
                flush=True,
            )
            return False

    def retry_original_message(self, msg):
        """Keep the original message available for retry."""

        try:
            self.consumer.seek(
                TopicPartition(
                    msg.topic(),
                    msg.partition(),
                    msg.offset(),
                )
            )

            print(
                f"Original message retained for retry | "
                f"Offset: {msg.offset()}",
                flush=True,
            )

            time.sleep(BASE_RETRY_DELAY)

        except Exception as error:
            print(
                f"Retry seek failed: {error}",
                flush=True,
            )

    def consume(self, topic: str):
        self.running = True

        # Handle Ctrl+C and Docker stop (SIGTERM)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

        self.consumer.subscribe(
            [topic],
            on_assign=self.on_assign,
            on_revoke=self.on_revoke,
        )

        print(
            f"Consumer started | "
            f"Group: {self.group_id} | Topic: {topic}",
            flush=True,
        )

        try:
            while self.running:
                msg = self.consumer.poll(1.0)

                if msg is None:
                    continue

                if msg.error():
                    print(
                        f"Kafka error: {msg.error()}",
                        flush=True,
                    )
                    continue

                print(
                    "Received message:",
                    msg.value(),
                    flush=True,
                )

                success, error = self.process_with_retries(msg)

                if success:
                    if not self.commit_offset(msg):
                        raise RuntimeError(
                            "Kafka offset commit failed. "
                            "Stopping consumer to avoid skipping messages."
                        )

                else:
                    dlt_success = self.publish_to_dlt(
                        msg,
                        error or "Unknown processing error",
                    )

                    if dlt_success:
                        if not self.commit_offset(msg):
                            raise RuntimeError(
                                "DLT offset commit failed. "
                                "Stopping consumer to avoid skipping messages."
                            )
                    else:
                        self.retry_original_message(msg)

        finally:
            print("Flushing DLT producer...", flush=True)
            self.dlt_producer.flush(timeout=10)

            self.consumer.close()

            print("Kafka consumer closed", flush=True)

    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown signals."""
        print(
            f"Shutdown signal received: {signum}",
            flush=True,
        )

        self.running = False

    def on_assign(self, consumer, partitions):
        print(
            f"Partitions assigned: {partitions}",
            flush=True,
        )


    def on_revoke(self, consumer, partitions):
        print(
            f"Partitions revoked: {partitions}",
            flush=True,
        )

if __name__ == "__main__":

    group_id = os.getenv(
        "KAFKA_CONSUMER_GROUP",
        "notification-group",
    )

    consumer = KafkaConsumerService(group_id=group_id)
    consumer.consume(topic="orders")
