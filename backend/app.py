from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.api.v1.routes import router as api_router
from backend.database.db import init_db

# Create FastAPI instance
app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init db
    await init_db()
    yield
    # Shutdown: cleanup (if needed)
    print("App shutting down...")

app = FastAPI(lifespan=lifespan)

# Add middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials = True,
    allow_methods = ['*'],
    allow_headers = ['*'],
)

# Include routers from different modules
app.include_router(api_router, prefix = '/api/v1', tags = ['routes'])

# Api routes
@app.get('/health')
def health_check():
    return {'status': 'ok'}

@app.get('/')
def root():
    return {'message': 'backend is active'}

