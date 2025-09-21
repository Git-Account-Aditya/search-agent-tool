from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1.routes import router as api_router

# Create FastAPI instance
app = FastAPI()

# Add middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins = ['*'],
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

