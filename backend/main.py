import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app, generate_latest
from sqlalchemy.future import select

from routers import auth, jobs, billing, ai
from core.observability import api_http_requests_total, api_latency_seconds, logger
from core.config import settings
from core.database import SessionLocal
from models import User, Credit
from core.security import get_password_hash

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "engineer@codeforge.ai"))
        if not result.scalars().first():
            user = User(email="engineer@codeforge.ai", hashed_password=get_password_hash("password"), role="Admin")
            db.add(user)
            await db.flush()
            db.add(Credit(user_id=user.id, balance=1000.0))
            await db.commit()
    yield

app = FastAPI(title="CodeForge API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus Metrics Endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.middleware("http")
async def add_process_time_header_and_metrics(request: Request, call_next):
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Record metrics
    endpoint = request.url.path
    if endpoint != "/metrics":
        api_http_requests_total.labels(method=request.method, endpoint=endpoint, status=response.status_code).inc()
        api_latency_seconds.labels(endpoint=endpoint).observe(process_time)
        
    return response

# Register Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(jobs.router, prefix="/jobs", tags=["Code Execution Jobs"])
app.include_router(billing.router, prefix="/credits", tags=["Billing & Credits"])
app.include_router(ai.router, prefix="/ai", tags=["AI Features"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
