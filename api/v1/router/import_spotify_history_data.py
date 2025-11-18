import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from api.v1.security.security import security


router = APIRouter(
    prefix="/api/v1",
    tags=["Import"],
)


@router.post("/import-data")
async def import_data(
    file: bytes,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    This endpoint handles data import operations from Spotify Extended History JSON files.
    It requires a valid authorization token.
    - **file**: The Spotify Extended History JSON file to be imported.
    - **credentials**: Authorization credentials provided by the user.
    """

    token = credentials.credentials
    expected_token = os.getenv("API_KEY")
    if not expected_token or token != expected_token:
        raise HTTPException(status_code=403, detail="Invalid or missing token.")

    # Here you would add the logic to process the uploaded file
    # For demonstration purposes, we'll just return a success message

    return {"status": "success", "message": "Data imported successfully."}
