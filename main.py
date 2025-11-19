import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials
from api.v1.security.security import security
from api.v1.router.import_spotify_history_data import router as import_router


app = FastAPI(
    title="ETL Spotify API",
    description="API for import Spotify Extended History JSON files.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(import_router)


@app.get("/")
async def read_root():
    """
    This is the root endpoint of the API.
    Redirects users to the documentation at /docs.
    """
    return RedirectResponse(url="/docs", status_code=302)


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify that the API is running.
    """
    return {"status": "ok"}


@app.get("/version")
async def get_version():
    """
    Endpoint to get the current version of the API.
    """
    return {"version": "1.0.0"}


@app.get("/check-auth")
async def check_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Endpoint to check if the provided authorization token is valid.
    """
    token = credentials.credentials
    expected_token = os.getenv("API_KEY")
    if not expected_token or token != expected_token:
        raise HTTPException(status_code=403, detail="Invalid or missing token.")
    return {"status": "authorized"}