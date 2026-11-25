"""Production AI Agent — Part 6 final project."""
import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from redis import RedisError

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import check_budget, record_cost
from app.rate_limiter import check_rate_limit
from app.redis_client import r, redis_healthy
from utils.mock_llm import ask as llm_ask


class JsonFormatter(logging.Formatter):
    def format(self, record):
        out = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "lvl": record.levelname,
            "event": record.getMessage(),
        }
        out.update(getattr(record, "extra_fields", {}))
        return json.dumps(out)


_handler = logging.StreamHandler()
_handler.setFormatter(JsonFormatter())
logger = logging.getLogger("agent")
logger.handlers = [_handler]
logger.setLevel(logging.INFO)
logger.propagate = False


def log(event: str, **fields):
    logger.info(event, extra={"extra_fields": fields})


@asynccontextmanager
async def lifespan(_app):
    log("startup", environment=settings.environment)
    yield
    # uvicorn already stops accepting connections and waits for in-flight requests on SIGTERM.
    r.close()
    log("shutdown")


app = FastAPI(title="Production AI Agent", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    user_id: str | None = None


@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    log("request", path=request.url.path, status=response.status_code, ms=round((time.time() - start) * 1000, 1))
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    if redis_healthy():
        return {"status": "ready"}
    return JSONResponse(status_code=503, content={"status": "redis unavailable"})


@app.post("/ask")
def ask(body: AskRequest, key: str = Depends(verify_api_key)):
    try:
        check_rate_limit(key)
        check_budget()
        answer = llm_ask(body.question)
        record_cost(len(body.question.split()) * 2, len(answer.split()) * 2)
    except RedisError:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    return {"question": body.question, "answer": answer}
