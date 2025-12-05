import os

from redis import Redis
from rq import Queue

# Redis connection and default queues for background jobs
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_conn = Redis.from_url(REDIS_URL)

# Dedicated queues so we can scale workers per queue if needed
crawl_queue = Queue("crawl", connection=redis_conn, default_timeout=900)
auto_update_queue = Queue("auto_update", connection=redis_conn, default_timeout=1800)
