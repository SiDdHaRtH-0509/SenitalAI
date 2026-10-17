"""Camera Registry endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.camera import CameraCreate, CameraResponse
from app.services.camera_service import get_all_cameras, register_camera

router = APIRouter()


@router.get("/cameras", response_model=List[CameraResponse], tags=["Cameras"])
def list_cameras(db: Session = Depends(get_db)) -> List[CameraResponse]:
    """Retrieve all configured CCTV camera edge nodes in the inventory."""
    return get_all_cameras(db)


@router.post("/cameras", response_model=CameraResponse, status_code=status.HTTP_201_CREATED, tags=["Cameras"])
def add_camera(camera_in: CameraCreate, db: Session = Depends(get_db)) -> CameraResponse:
    """Register or update a camera device in the surveillance registry."""
    return register_camera(db, camera_in)
