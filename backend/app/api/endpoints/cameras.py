"""Camera Registry and Worker Management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.security import ROLE_ADMIN, ROLE_OPERATOR, ROLE_SERVICE
from app.database import get_db
from app.models.user import User
from app.schemas.camera import CameraCreate, CameraResponse, CameraStartRequest, CameraWorkerStatus
from app.services.camera_service import get_all_cameras, get_camera_by_id, register_camera
from app.services.camera_worker import worker_manager
from app.services.zone_service import get_zone_by_id
from app.services.audit_service import record_audit

router = APIRouter()


@router.get("/cameras", response_model=List[CameraResponse], tags=["Cameras"])
def list_cameras(
    current_user: User = Depends(require_roles([ROLE_OPERATOR, ROLE_ADMIN, ROLE_SERVICE])),
    db: Session = Depends(get_db),
) -> List[CameraResponse]:
    """Retrieve all configured CCTV camera edge nodes with live worker telemetry.
    
    Protected: Requires authenticated OPERATOR, ADMIN, or SERVICE identity.
    """
    cameras = get_all_cameras(db)
    statuses = worker_manager.get_all_statuses()
    
    response_list = []
    for cam in cameras:
        cam_resp = CameraResponse.model_validate(cam)
        cam_resp.worker_status = statuses.get(cam.camera_id) or worker_manager.get_status(cam.camera_id)
        response_list.append(cam_resp)
        
    return response_list


@router.get("/cameras/{camera_id}", response_model=CameraResponse, tags=["Cameras"])
def get_camera(
    camera_id: str,
    current_user: User = Depends(require_roles([ROLE_OPERATOR, ROLE_ADMIN, ROLE_SERVICE])),
    db: Session = Depends(get_db),
) -> CameraResponse:
    """Retrieve a single camera device with live worker status."""
    camera = get_camera_by_id(db, camera_id)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found.",
        )
    cam_resp = CameraResponse.model_validate(camera)
    cam_resp.worker_status = worker_manager.get_status(camera_id)
    return cam_resp


@router.post("/cameras", response_model=CameraResponse, status_code=status.HTTP_201_CREATED, tags=["Cameras"])
def add_camera(
    camera_in: CameraCreate,
    current_admin: User = Depends(require_roles([ROLE_ADMIN])),
    db: Session = Depends(get_db),
) -> CameraResponse:
    """Register or update a camera device in the surveillance registry (Admin only)."""
    camera = register_camera(db, camera_in)
    record_audit(
        db=db,
        action="CAMERA_REGISTERED",
        target_type="camera",
        actor_username=current_admin.username,
        actor_role=current_admin.role,
        target_id=camera.camera_id,
        outcome="SUCCESS",
        details=f"Name: {camera.name}, Zone: {camera.zone_id}",
    )
    cam_resp = CameraResponse.model_validate(camera)
    cam_resp.worker_status = worker_manager.get_status(camera.camera_id)
    return cam_resp


@router.post("/cameras/{camera_id}/start", response_model=CameraWorkerStatus, tags=["Cameras"])
def start_camera_worker(
    camera_id: str,
    start_req: Optional[CameraStartRequest] = None,
    current_user: User = Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR])),
    db: Session = Depends(get_db),
) -> CameraWorkerStatus:
    """Start continuous video ingestion and CV analytics for a camera (Admin or Operator)."""
    camera = get_camera_by_id(db, camera_id)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found.",
        )

    zone = get_zone_by_id(db, camera.zone_id) if camera.zone_id else None
    replay_mode = start_req.replay_mode if start_req else False

    worker_status = worker_manager.start_camera(camera=camera, zone=zone, replay_mode=replay_mode)

    record_audit(
        db=db,
        action="CAMERA_WORKER_STARTED",
        target_type="camera",
        actor_username=current_user.username,
        actor_role=current_user.role,
        target_id=camera_id,
        outcome="SUCCESS",
        details=f"Started analytics worker for {camera.name} (replay_mode={replay_mode})",
    )

    return worker_status


@router.post("/cameras/{camera_id}/stop", response_model=CameraWorkerStatus, tags=["Cameras"])
def stop_camera_worker(
    camera_id: str,
    current_user: User = Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR])),
    db: Session = Depends(get_db),
) -> CameraWorkerStatus:
    """Stop continuous video ingestion and CV analytics for a camera (Admin or Operator)."""
    camera = get_camera_by_id(db, camera_id)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found.",
        )

    worker_status = worker_manager.stop_camera(camera_id)

    record_audit(
        db=db,
        action="CAMERA_WORKER_STOPPED",
        target_type="camera",
        actor_username=current_user.username,
        actor_role=current_user.role,
        target_id=camera_id,
        outcome="SUCCESS",
        details=f"Stopped analytics worker for {camera.name}",
    )

    return worker_status


@router.get("/cameras/{camera_id}/status", response_model=CameraWorkerStatus, tags=["Cameras"])
def get_camera_worker_status(
    camera_id: str,
    current_user: User = Depends(require_roles([ROLE_OPERATOR, ROLE_ADMIN, ROLE_SERVICE])),
    db: Session = Depends(get_db),
) -> CameraWorkerStatus:
    """Retrieve real-time processing metrics, FPS, latency, and connection status for a camera worker."""
    camera = get_camera_by_id(db, camera_id)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found.",
        )

    return worker_manager.get_status(camera_id)


@router.get("/cameras/{camera_id}/snapshot", tags=["Cameras"])
def get_camera_snapshot(
    camera_id: str,
    current_user: User = Depends(require_roles([ROLE_OPERATOR, ROLE_ADMIN, ROLE_SERVICE])),
    db: Session = Depends(get_db),
):
    """Retrieve the latest real-time frame snapshot (JPEG) from an active camera worker."""
    camera = get_camera_by_id(db, camera_id)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found.",
        )

    snapshot_bytes = worker_manager.get_camera_snapshot(camera_id)
    if not snapshot_bytes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No snapshot available. Start camera analytics worker first.",
        )

    from fastapi.responses import Response
    return Response(content=snapshot_bytes, media_type="image/jpeg")

