# src/core/geometry.py
from dataclasses import dataclass

@dataclass
class LaneDefinition:
    """
    Represents the normalized X-axis geometric constraint for a specific film side.
    This defines the 'strip' in which all perforations on this side must align.
    """
    side: str  # 'LEFT' or 'RIGHT'
    x: int
    width: int

    @property
    def end_x(self) -> int:
        return self.x + self.width
    
    def to_dict(self):
        return {"side": self.side, "x": self.x, "width": self.width}

@dataclass
class AnchorDefinition:
    """
    Represents the Y-axis geometric constraint for a specific perforation.
    This defines where a hole is expected to start and end vertically.
    """
    id: str
    lane_side: str # References LaneDefinition.side
    y: int
    height: int

    @property
    def end_y(self) -> int:
        return self.y + self.height
    
    def to_dict(self):
        return {"id": self.id, "lane_side": self.lane_side, "y": self.y, "height": self.height}
