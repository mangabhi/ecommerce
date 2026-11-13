from src.kafka.producer import kafka_producer

event = {
    "event_type": "OrderCreated",
    "order_id": "ORD104",
    "amount": 2500
}

kafka_producer.publish("orders", event)

remaining = kafka_producer.flush(timeout=10)

print(f"Messages still waiting: {remaining}")