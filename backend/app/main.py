"""FastAPI entrypoint for the wind forecast analytics API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import dashboard

app = FastAPI(
    title="Wind Forecast Analytics API",
    description=(
        "National UK wind generation forecasts vs actuals for day-ahead procurement decisions. "
        "Data source: Elexon BMRS FUELHH + WINDFOR."
    ),
    version="1.0.0",
)

origins = [origin.strip() for origin in settings.frontend_origin.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
