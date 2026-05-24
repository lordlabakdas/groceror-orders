import os

RABBITMQ_HOST   = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT   = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER   = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS   = os.getenv("RABBITMQ_PASS", "guest")
RABBITMQ_VHOST  = os.getenv("RABBITMQ_VHOST", "/")
MONGO_URI       = os.getenv("MONGO_URI", "mongodb://localhost:27017")
API_HOST        = os.getenv("API_HOST", "0.0.0.0")
API_PORT        = int(os.getenv("API_PORT", 8001))
METRICS_BACKEND = os.getenv("METRICS_BACKEND", "prometheus")
PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "")
QUEUE_NAME      = "order_queue"
DLQ_NAME        = "order_queue.dlq"
DLX_EXCHANGE    = "dlx"
