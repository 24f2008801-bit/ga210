from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import time

app = FastAPI()

# ==========================================
# CONFIGURATION
# ==========================================
EMAIL = "24f2008801@ds.study.iitm.ac.in"

WINDOW = 10   # seconds
LIMIT = 10    # requests per window

rate_limit = {}

# ==========================================
# CORS
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-fs0hy9.example.com",
        "https://exam.sanand.work",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# MIDDLEWARE
# ==========================================
@app.middleware("http")
async def middleware(request: Request, call_next):

    # Let CORS handle preflight requests
    if request.method == "OPTIONS":
        return await call_next(request)

    # -----------------------
    # Request Context
    # -----------------------
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # -----------------------
    # Rate Limiting
    # -----------------------
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

# ==========================================
# ROOT
# ==========================================
@app.get("/")
async def root():
    return {"status": "ok"}

# ==========================================
# /PING
# ==========================================
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }