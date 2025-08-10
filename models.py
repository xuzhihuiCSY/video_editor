
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Clip:
    path: str
    in_ms: int = 0
    out_ms: Optional[int] = None
    start_ms_on_timeline: int = 0
    track_index: int = 0

@dataclass
class Track:
    name: str
    clips: List[Clip] = field(default_factory=list)

@dataclass
class Sequence:
    name: str = "Sequence 01"
    tracks: List[Track] = field(default_factory=lambda: [Track("V1"), Track("V2")])
    duration_ms: int = 60_000
