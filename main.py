@app.middleware("http")
async def middleware(request: Request, call_next):

    # Let CORS middleware handle browser preflight
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
                "X-Request-ID": request_id
            },
            content={"detail": "Rate limit exceeded"},
        )

    history.append(now)
    rate_limit[client_id] = history

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response