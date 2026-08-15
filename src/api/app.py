import time
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.utils.logger import logger
from src.database.connection import init_db
from src.database.seed_data import seed_database_and_samples
from src.domain.exceptions import AttritionSystemException
from src.api.routes import predict, analytics

# Initialize FastAPI Application
app = FastAPI(
    title=settings.APP_NAME,
    description="Production Enterprise REST API for Employee Attrition Prediction, SHAP Explainable AI, and HR Retention Recommendations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits cross-origin calls from Streamlit and enterprise clients
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Request Logging & Timing Middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    path = request.url.path
    method = request.method
    
    logger.info(f"Incoming Request: {method} {path}")
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f"Completed {method} {path} | Status: {response.status_code} | Duration: {process_time:.2f}ms")
        return response
    except Exception as exc:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"Failed {method} {path} | Duration: {process_time:.2f}ms | Error: {str(exc)}")
        raise exc

# Custom Exception Handler for Domain Exceptions
@app.exception_handler(AttritionSystemException)
async def domain_exception_handler(request: Request, exc: AttritionSystemException):
    logger.error(f"Domain Exception Triggered: {exc.message} | Details: {exc.details}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.message,
            "details": exc.details or "An application domain error occurred."
        }
    )

# Register API Routers
app.include_router(predict.router)
app.include_router(analytics.router)

# Application Startup Event Handler
@app.on_event("startup")
def on_startup():
    logger.info("Initializing Enterprise Attrition Prediction API System...")
    try:
        init_db()
        seed_database_and_samples()
        logger.info("Startup complete. System is ready to accept API requests.")
    except Exception as e:
        logger.error(f"Error during startup initialization: {str(e)}")

# Root Endpoint
@app.get("/", tags=["Health"])
def root():
    return {
        "system": settings.APP_NAME,
        "status": "Online",
        "version": "1.0.0",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
