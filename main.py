from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import uuid
import time

app = FastAPI()

EMAIL = "24f2008801@ds.study.iitm.ac.in"

WINDOW = 10
LIMIT = 10

rate_limit = {}

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-fs0hy9.example.com",
        "https://exam.sanand.work",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Request Context + Rate Limit
# -----------------------------
@app.middleware("http")
async def context_and_rate_limit(request: Request, call_next):

    # Let CORS middleware answer preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    # Request ID
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # Rate limiting
    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    history = rate_limit.get(client_id, [])
    history = [t for t in history if now - t < WINDOW]

    if len(history) >= LIMIT:
        return JSONResponse(
            status_code=429,
            headers={
                "Retry-After": "10",
                "X-Request-ID": request_id,
            },
            content={"detail": "Rate limit exceeded"},
        )

    history.append(now)
    rate_limit[client_id] = history

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# -----------------------------
# Explicit OPTIONS handler
# -----------------------------
@app.options("/ping")
async def options_ping():
    return Response(status_code=200)


# -----------------------------
# Health Check
# -----------------------------
@app.get("/")
async def root():
    return {"status": "ok"}


# -----------------------------
# Ping Endpoint
# -----------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }