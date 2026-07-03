from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

app = FastAPI()

# =========================
# CORS (STRICT)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-fs0hy9.example.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# RATE LIMIT STORE
# =========================
RATE_LIMIT = {}
WINDOW = 10  # seconds
LIMIT = 10   # requests per window

EMAIL = "your_email@example.com"  # replace if needed


# =========================
# MIDDLEWARE: REQUEST CONTEXT + RATE LIMIT
# =========================
@app.middleware("http")
async def middleware(request: Request, call_next):

    # -------------------------
    # REQUEST ID HANDLING
    # -------------------------
    req_id = request.headers.get("X-Request-ID")
    if not req_id:
        req_id = str(uuid.uuid4())

    request.state.request_id = req_id

    # -------------------------
    # RATE LIMIT BY CLIENT ID
    # -------------------------
    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    if client_id not in RATE_LIMIT:
        RATE_LIMIT[client_id] = []

    # keep only last 10 seconds
    RATE_LIMIT[client_id] = [
        t for t in RATE_LIMIT[client_id]
        if now - t < WINDOW
    ]

    if len(RATE_LIMIT[client_id]) >= LIMIT:
        return Response(
            content='{"detail":"Rate limit exceeded"}',
            status_code=429,
            media_type="application/json"
        )

    RATE_LIMIT[client_id].append(now)

    # -------------------------
    # PROCESS REQUEST
    # -------------------------
    response = await call_next(request)

    # attach request id to response header
    response.headers["X-Request-ID"] = req_id

    return response


# =========================
# ROUTE
# =========================
@app.get("/ping")
def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
