from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import json
from pathlib import Path
import time
import uuid

@dataclass
class Clip:
    id: str
    name: str
    src_path: str      # original file
    work_path: str     # safe temp copy used by the editor
    duration: float
    fps: float
    width: int
    height: int
    in_point: float = 0.0
    out_point: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> 'Clip':
        return Clip(**d)

class Project:
    def __init__(self):
        self.version = 1
        self.created = time.time()
        self.modified = self.created
        self.clips: List[Clip] = []

    def add_clip(self, clip: Clip):
        self.clips.append(clip)
        self.touch()

    def touch(self):
        self.modified = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "created": self.created,
            "modified": self.modified,
            "clips": [c.to_dict() for c in self.clips],
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> 'Project':
        p = Project()
        p.version = d.get("version", 1)
        p.created = d.get("created", p.created)
        p.modified = d.get("modified", p.modified)
        p.clips = [Clip.from_dict(c) for c in d.get("clips", [])]
        return p

    def save(self, path: Path):
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @staticmethod
    def load(path: Path) -> 'Project':
        data = json.loads(path.read_text(encoding="utf-8"))
        return Project.from_dict(data)
