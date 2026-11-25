"""Cost guard: accumulate spend in Redis per day; over budget -> 402."""
from datetime import date

from fastapi import HTTPException

from app.config import settings
from app.redis_client import r

# USD per 1K tokens (gpt-4o-mini reference)
PRICE_INPUT_PER_1K = 0.00015
PRICE_OUTPUT_PER_1K = 0.0006


def _key() -> str:
    return f"cost:{date.today().isoformat()}"


def check_budget() -> None:
    if float(r.get(_key()) or 0) >= settings.daily_budget_usd:
        raise HTTPException(status_code=402, detail="Daily budget exceeded")


def record_cost(input_tokens: int, output_tokens: int) -> float:
    cost = input_tokens / 1000 * PRICE_INPUT_PER_1K + output_tokens / 1000 * PRICE_OUTPUT_PER_1K
    k = _key()
    r.incrbyfloat(k, cost)
    r.expire(k, 2 * 86400)
    return cost
