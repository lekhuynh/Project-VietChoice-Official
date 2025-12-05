from rq.job import Job
from redis.exceptions import RedisError

from ..rq_conn import redis_conn


def get_job_status(job_id: str) -> dict:
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except RedisError:
        return {"job_id": job_id, "status": "not_found"}
    except Exception:
        return {"job_id": job_id, "status": "not_found"}

    return {
        "job_id": job_id,
        "status": job.get_status(),
        "result": job.result if job.is_finished else None,
    }
