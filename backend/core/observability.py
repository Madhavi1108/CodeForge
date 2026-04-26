import structlog
import logging
from prometheus_client import Counter, Histogram, Gauge

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus Metrics
jobs_enqueued_total = Counter("jobs_enqueued_total", "Total number of jobs enqueued", ["language", "priority"])
api_http_requests_total = Counter("api_http_requests_total", "Total HTTP Requests", ["method", "endpoint", "status"])
api_latency_seconds = Histogram("api_latency_seconds", "API Latency in seconds", ["endpoint"])
queue_length = Gauge("queue_length", "Current number of items in queue", ["topic"])
