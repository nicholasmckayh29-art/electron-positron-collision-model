from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR / ".env")

from routers.data import router as data_router  # noqa: E402
from routers.quantum import router as quantum_router  # noqa: E402

app = FastAPI(
    title="Quantum Particle Collision Visualizer",
    description="Upload dielectron collision data, identify outliers, match to particles, run quantum analysis",
    version="1.1.0"
)

# CORS - allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(data_router, prefix="/api", tags=["data"])
app.include_router(quantum_router, prefix="/api/quantum", tags=["quantum"])


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Quantum Particle Collision Visualizer API"}


@app.get("/api/health")
def api_health():
    """API health check."""
    return {"status": "ok"}
