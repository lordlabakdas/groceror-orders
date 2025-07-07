import logging
import os
import time

import pika

from order import Order

logger = logging.getLogger(__name__)


def setup_rabbit_connection():
    """Establish connection to RabbitMQ"""
    try:
        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER", "guest"), os.getenv("RABBITMQ_PASS", "guest")
        )
        parameters = pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )
        return pika.BlockingConnection(parameters)
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
        raise


def start_consumer():
    """Start consuming messages from RabbitMQ"""
    while True:
        try:
            connection = setup_rabbit_connection()
            channel = connection.channel()

            # Declare queue with durability
            channel.queue_declare(queue="order_queue", durable=True)

            # Set up consumer
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(
                queue="order_queue", on_message_callback=Order.save_order_info
            )

            print("Email service started. Waiting for messages...")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            logger.error("Lost connection to RabbitMQ. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            time.sleep(5)


if __name__ == "__main__":
    import threading

    # Start message consumer in a separate thread
    consumer_thread = threading.Thread(target=start_consumer)
    consumer_thread.daemon = False
    consumer_thread.start()
