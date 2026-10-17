"""SQLAlchemy ORM model for Restricted Zones."""

import json
from typing import List
from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class ZoneModel(Base):
    """Database model for calibrated restricted-zone boundary polygons."""

    __tablename__ = "restricted_zones"

    zone_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    camera_id = Column(String(64), nullable=False, index=True)
    status = Column(String(24), nullable=False, default="ACTIVE")
    vertices_json = Column(Text, nullable=False)
    reference_strategy = Column(String(32), nullable=False, default="bottom_center")
    incursions_today = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=False)

    @property
    def vertices(self) -> List[List[float]]:
        """Parsed vertices list."""
        if not self.vertices_json:
            return []
        try:
            return json.loads(self.vertices_json)
        except Exception:
            return []

    @vertices.setter
    def vertices(self, val: List[List[float]]) -> None:
        self.vertices_json = json.dumps(val or [])
