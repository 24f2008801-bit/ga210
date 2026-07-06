from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time

app = FastAPI()

EMAIL = "24f2008801@ds.study.iitm.ac.in"

WINDOW = 10
LIMIT = 10

rate_limit = {}


# --------------------------------------------------
# Request Context Middleware
# --------------------------------------------------
class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response


# --------------------------------------------------
# Rate Limit Middleware
# --------------------------------------------------
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        # Skip preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Ensure request_id always exists
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            request.state.request_id = request_id

        client_id = request.headers.get("X-Client-Id")

        # Requests without X-Client-Id each get their own bucket
        if client_id is None:
            client_id = request_id

        now = time.time()

        history = rate_limit.get(client_id, [])
        history = [t for t in history if now - t < WINDOW]

        if len(history) >= LIMIT:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )
            response.headers["Retry-After"] = str(WINDOW)
            response.headers["X-Request-ID"] = request_id
            return response

        history.append(now)
        rate_limit[client_id] = history

        return await call_next(request)


# --------------------------------------------------
# CORS
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-fs0hy9.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=[
        "X-Request-ID",
        "X-Client-Id",
        "Content-Type",
    ],
    expose_headers=[
        "X-Request-ID",
        "Retry-After",
    ],
)

# Middleware execution is reverse order of addition
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)


# --------------------------------------------------
# Root
# --------------------------------------------------
@app.get("/")
async def root():
    return {"status": "ok"}


# --------------------------------------------------
# Ping
# --------------------------------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }