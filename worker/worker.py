import os

if os.name == "nt":  
    # Windows → dùng SimpleWorker
    from rq import SimpleWorker as Worker
else:
    # Linux / Docker → dùng Worker bình thường (có fork)
    from rq import Worker

from worker.config import settings
from app.rq_conn import redis_conn


def main():
    print("[WORKER] Connected to:", redis_conn)
    print("[WORKER] Queues:", settings.queues)
    print(f"[WORKER] OS: {os.name} (using {'SimpleWorker' if os.name=='nt' else 'Worker'})")

    worker = Worker(settings.queues, connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
