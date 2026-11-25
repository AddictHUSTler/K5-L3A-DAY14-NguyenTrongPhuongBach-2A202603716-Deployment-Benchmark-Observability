"""Sliding-window rate limit per API key, stored in Redis (shared across workers, survives restarts)."""
import time
import uuid

from fastapi import HTTPException

from app.config import settings
from app.redis_client import r


def check_rate_limit(key: str) -> None:
    now = time.time()
    rk = f"rate:{key}"
    r.zremrangebyscore(rk, 0, now - 60)
    if r.zcard(rk) >= settings.rate_limit_per_minute:
        oldest = r.zrange(rk, 0, 0, withscores=True)
        retry = max(1, int(60 - (now - oldest[0][1])) + 1) if oldest else 60
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers={"Retry-After": str(retry)})
    r.zadd(rk, {f"{now}:{uuid.uuid4().hex[:8]}": now})
    r.expire(rk, 61)
