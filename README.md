# groceror-orders

Microservice that consumes order events from RabbitMQ, stores them in MongoDB, and exposes analytics endpoints and Prometheus metrics for Grafana dashboarding.

Published by the [groceror](https://github.com/lordlabakdas/groceror) main service. Can run as a long-running container or locally against any MongoDB instance.

---

## Events consumed

| Event | Trigger |
|---|---|
| `order_created` | New order placed via `POST /order/create-order` |

Orders are stored in the `orders` database, `client_orders` collection. Upsert is keyed on `order_id` so redelivered messages are safe to process again.

---

## Running alongside groceror

groceror runs as a bare Python process (`make run`) and expects RabbitMQ on `localhost:5672`. groceror-orders runs in Docker Compose and connects to that same broker via `host.docker.internal`.

**1. Start RabbitMQ on your host** (if not already running):

```bash
# macOS
brew services start rabbitmq

# Linux
sudo systemctl start rabbitmq-server

# or via Docker (standalone)
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

**2. Start groceror:**

```bash
cd /path/to/groceror
make run   # starts on localhost:8000
```

**3. Configure MongoDB URI:**

Create a `.env` file in the project root (or export the variable):

```dotenv
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>/?retryWrites=true&w=majority
```

A local MongoDB also works:

```dotenv
MONGO_URI=mongodb://localhost:27017
```

**4. Start groceror-orders:**

```bash
docker compose up --build
```

The compose stack picks up `MONGO_URI` from your `.env` file automatically.

**Verify it's working:**

Place an order on groceror (`POST /order/create-order`), then check:

```bash
# order landed in MongoDB
# (use MongoDB Compass → connect to your Atlas cluster or localhost:27017)

# metric incremented
curl -s localhost:8001/metrics | grep groceror_orders_events_total
```

Open Grafana at http://localhost:3002 (admin / admin) — the **Order Events** dashboard shows activity in real time.

> **Note:** If RabbitMQ refuses the connection with a 403 auth error, see the [authentication fix](#rabbitmq-authentication) section below.

---

## Running with Docker Compose

The compose stack includes groceror-orders, Prometheus, and Grafana. MongoDB is external (Atlas or a local instance you provide via `MONGO_URI`).

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| groceror-orders API | http://localhost:8001 |
| Prometheus | http://localhost:9091 |
| Grafana | http://localhost:3002 (admin / admin) |

The Grafana dashboard (`Order Events`) is provisioned automatically on startup.

---

## Running locally (without Docker)

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # for tests only

python main.py
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `RABBITMQ_HOST` | `localhost` | RabbitMQ broker hostname |
| `RABBITMQ_PORT` | `5672` | RabbitMQ broker port |
| `RABBITMQ_USER` | `guest` | RabbitMQ username |
| `RABBITMQ_PASS` | `guest` | RabbitMQ password |
| `RABBITMQ_VHOST` | `/` | RabbitMQ virtual host |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection URI |
| `API_HOST` | `0.0.0.0` | FastAPI bind address |
| `API_PORT` | `8001` | FastAPI port |
| `METRICS_BACKEND` | `prometheus` | `prometheus` (container) or `pushgateway` (Lambda) |
| `PUSHGATEWAY_URL` | _(empty)_ | Pushgateway URL, required when `METRICS_BACKEND=pushgateway` |

### Using a `.env` file

```dotenv
MONGO_URI=mongodb+srv://user:pass@cluster/?retryWrites=true&w=majority
RABBITMQ_USER=groceror
RABBITMQ_PASS=changeme
```

---

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Returns `{"status": "ok"}` |
| `GET /metrics` | Prometheus metrics (text/plain) |
| `GET /analytics/summary` | Total revenue and order count |
| `GET /analytics/most-ordered-items` | Top N items by order frequency |
| `GET /analytics/revenue-by-item` | Top N items by revenue |
| `GET /analytics/orders-per-day` | Daily order counts and revenue |

All analytics endpoints accept an optional `limit` query parameter (default 10, max 100; orders-per-day max 365).

---

## Metrics

| Metric | Type | Labels | Description |
|---|---|---|---|
| `groceror_orders_events_total` | Counter | `event_type` | Successfully stored events |
| `groceror_orders_processing_errors_total` | Counter | `event_type`, `reason` | Validation, schema, or DB errors |
| `groceror_orders_consumer_up` | Gauge | — | `1` when connected, `0` otherwise |

---

## RabbitMQ authentication

By default, RabbitMQ's `guest` user only accepts connections from `localhost`. Since groceror-orders runs inside Docker, it connects from a different IP and will get a 403 refused error.

**Fix — allow guest from remote hosts (dev only):**

```bash
# macOS
echo "loopback_users = none" >> /opt/homebrew/etc/rabbitmq/rabbitmq.conf
brew services restart rabbitmq

# Linux
echo "loopback_users = none" | sudo tee -a /etc/rabbitmq/rabbitmq.conf
sudo systemctl restart rabbitmq-server
```

Then restart the stack: `docker compose restart groceror-orders`

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```
