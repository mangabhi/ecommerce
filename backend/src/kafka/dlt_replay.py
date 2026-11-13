
import json
import os

from confluent_kafka import Consumer, Producer


class DLTReplayService:

    def __init__(self):
        bootstrap_servers = os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092",
        )

        # Consumer reads failed events from the DLT.
        self.consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": "dlt-replay-group",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "enable.auto.offset.store": False,
        })

        # Producer republishes original events.
        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
        })

        print("DLT Replay Service initialized", flush=True)

    def replay_message(self, msg):
        """Republish the original event from a DLT message."""

        try:
            dlt_event = json.loads(
                msg.value().decode("utf-8")
            )

            original_topic = dlt_event["original_topic"]
            original_message = dlt_event["original_message"]

            # Validate the original event before publishing.
            original_event = json.loads(original_message)
            if not isinstance(original_event, dict):
                raise ValueError("Original event must be a JSON object")

            if not original_event.get("event_id"):
                raise ValueError("Original event is missing event_id")

            delivery_result = {
                "success": False,
                "error": None,
            }

            def delivery_report(err, kafka_msg):
                if err is not None:
                    delivery_result["error"] = str(err)
                else:
                    delivery_result["success"] = True

            self.producer.produce(
                topic=original_topic,
                key=msg.key(),
                value=original_message,
                callback=delivery_report,
            )

            remaining = self.producer.flush(timeout=10)

            if remaining > 0 or not delivery_result["success"]:
                raise RuntimeError(
                    delivery_result["error"]
                    or "Replay delivery timed out"
                )

            print(
                f"Event replayed successfully | "
                f"Event ID: {original_event['event_id']} | "
                f"Topic: {original_topic}",
                flush=True,
            )

            return True

        except Exception as error:
            print(
                f"DLT replay failed: {error}",
                flush=True,
            )
            return False
    def consume_and_replay(self, dlt_topic: str):
        """Consume DLT messages and replay them to their original topic."""

        self.consumer.subscribe([dlt_topic])

        print(
            f"DLT replay started | Topic: {dlt_topic}",
            flush=True,
        )

        try:
            while True:
                msg = self.consumer.poll(1.0)

                if msg is None:
                    continue

                if msg.error():
                    print(
                        f"Kafka consumer error: {msg.error()}",
                        flush=True,
                    )
                    continue

                success = self.replay_message(msg)

                if success:
                    try:
                        self.consumer.commit(
                            message=msg,
                            asynchronous=False,
                        )

                        print(
                            f"DLT offset committed: "
                            f"{msg.topic()} [{msg.partition()}] "
                            f"offset {msg.offset() + 1}",
                            flush=True,
                        )

                    except Exception as error:
                        print(
                            f"DLT offset commit failed: {error}",
                            flush=True,
                        )
                        break

                else:
                    print(
                        "Replay failed. DLT offset not committed.",
                        flush=True,
                    )
                    break

        except KeyboardInterrupt:
            print("DLT replay interrupted", flush=True)

        finally:
            self.producer.flush(timeout=10)
            self.consumer.close()
            print("DLT replay service closed", flush=True)


if __name__ == "__main__":
    replay_service = DLTReplayService()
    replay_service.consume_and_replay(
        dlt_topic="orders.DLT"
    )