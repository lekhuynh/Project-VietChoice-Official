import json
import logging
from typing import Any, Optional

from .rq_conn import redis_conn

logger = logging.getLogger(__name__)


def get_json(key: str) -> Optional[Any]:
    try:
        raw = redis_conn.get(key)
        if raw is None:
            logger.debug("cache miss: %s", key)
            return None
        logger.debug("cache hit: %s", key)
        return json.loads(raw)
    except Exception as exc:
        logger.debug("cache error on get %s: %s", key, exc)
        return None


def set_json(key: str, value: Any, ttl_seconds: int) -> None:
    try:
        # default=str giúp serialize Decimal/UUID/etc thay vì lỗi
        redis_conn.setex(key, ttl_seconds, json.dumps(value, default=str))
        logger.debug("cache set: %s ttl=%s", key, ttl_seconds)
    except Exception as exc:
        logger.debug("cache error on set %s: %s", key, exc)


def delete(key: str) -> None:
    try:
        redis_conn.delete(key)
        logger.debug("cache delete: %s", key)
    except Exception as exc:
        logger.debug("cache error on delete %s: %s", key, exc)
