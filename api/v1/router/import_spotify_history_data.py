import os
import json
import tempfile
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from api.v1.security.security import security
from modules.import_file_module import import_spotify_history_file

# Charger les variables d'environnement
load_dotenv()

router = APIRouter(
    prefix="/api/v1",
    tags=["Import"],
)


def get_database_session():
    """
    Create and return a new SQLAlchemy session.
    """
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT')
        db_name = os.getenv('DB_NAME')
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


@router.post("/import-data")
async def import_data(
    file: UploadFile = File(...),
    user_id: str = "default_user",
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Import Spotify Extended History JSON files into the database.
    
    This endpoint handles data import operations from Spotify Extended History JSON files.
    It requires a valid authorization token.
    
    - **file**: The Spotify Extended History JSON file to be imported (UploadFile).
    - **user_id**: The user ID to associate with the imported history (default: "default_user").
    - **credentials**: Authorization credentials provided by the user.
    
    Returns:
        Dictionary with import statistics (artists, albums, tracks, history counts).
    """
    # Verify the authorization token
    token = credentials.credentials
    expected_token = os.getenv("API_KEY")
    if not expected_token or token != expected_token:
        raise HTTPException(status_code=403, detail="Invalid or missing token.")
    
    # Verify that the uploaded file is a JSON file
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be a JSON file.")
    
    session = None
    try:
        # Read the content of the file
        content = await file.read()
        
        # Create a temporary file to store the JSON
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Create a database session
        session = get_database_session()
        
        # Import the file
        stats = import_spotify_history_file(session, tmp_file_path, user_id)
        
        # Clean up the temporary file
        os.unlink(tmp_file_path)
        
        return {
            "status": "success",
            "message": f"Data from {file.filename} imported successfully.",
            "statistics": {
                "artists_imported": stats['artists'],
                "albums_imported": stats['albums'],
                "tracks_imported": stats['tracks'],
                "history_entries_imported": stats['history']
            }
        }
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    
    except Exception as e:
        if session:
            session.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
    
    finally:
        if session:
            session.close()


@router.post("/import-multiple")
async def import_multiple_files(
    files: List[UploadFile] = File(...),
    user_id: str = "default_user",
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Import multiple Spotify Extended History JSON files into the database.
    
    - **files**: List of Spotify Extended History JSON files to be imported.
    - **user_id**: The user ID to associate with the imported history (default: "default_user").
    - **credentials**: Authorization credentials provided by the user.
    
    Returns:
        Dictionary with cumulative import statistics for all files.
    """
    # Verify the authorization token
    token = credentials.credentials
    expected_token = os.getenv("API_KEY")
    if not expected_token or token != expected_token:
        raise HTTPException(status_code=403, detail="Invalid or missing token.")
    
    total_stats = {'artists': 0, 'albums': 0, 'tracks': 0, 'history': 0}
    imported_files = []
    errors = []
    
    session = None
    try:
        session = get_database_session()
        
        for file in files:
            try:
                # Verify that the uploaded file is a JSON file
                if not file.filename.endswith('.json'):
                    errors.append(f"{file.filename}: Not a JSON file")
                    continue
                
                # Read the content of the file
                content = await file.read()
                
                # Create a temporary file
                with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as tmp_file:
                    tmp_file.write(content)
                    tmp_file_path = tmp_file.name
                
                # Import the file
                stats = import_spotify_history_file(session, tmp_file_path, user_id)
                
                # Accumulate the stats
                for key in total_stats:
                    total_stats[key] += stats[key]
                
                imported_files.append(file.filename)
                
                # Clean up the temporary file
                os.unlink(tmp_file_path)
            
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
        
        return {
            "status": "success" if imported_files else "failed",
            "message": f"{len(imported_files)} file(s) imported successfully.",
            "imported_files": imported_files,
            "errors": errors if errors else None,
            "total_statistics": {
                "artists_imported": total_stats['artists'],
                "albums_imported": total_stats['albums'],
                "tracks_imported": total_stats['tracks'],
                "history_entries_imported": total_stats['history']
            }
        }
    
    except Exception as e:
        if session:
            session.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
    
    finally:
        if session:
            session.close()
