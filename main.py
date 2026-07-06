from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import time

app = FastAPI()

EMAIL = "24f2008801@ds.study.iitm.ac.in"

WINDOW = 10
LIMIT = 10

rate_limit = {}

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

# --------------------------------------------------
# Request Context + Rate Limiting
# --------------------------------------------------
@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):

    # Request ID
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # Skip rate limiting for CORS preflight
    if request.method != "OPTIONS":

        client_id = request.headers.get("X-Client-Id")
        now = time.time()

        history = rate_limit.get(client_id, [])
        history = [t for t in history if now - t < WINDOW]

        if len(history) >= LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={
                    "Retry-After": str(WINDOW),
                    "X-Request-ID": request_id,
                },
            )

        history.append(now)
        rate_limit[client_id] = history

    response = await call_next(request)

    # Echo the request ID in every response
    response.headers["X-Request-ID"] = request_id

    return response


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