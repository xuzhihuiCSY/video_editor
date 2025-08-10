import tempfile
import shutil
from pathlib import Path

class MediaStore:
    """Manages a session temp directory with safe working copies of media."""
    def __init__(self, prefix: str = "prlite_"):
        self.temp_dir = Path(tempfile.mkdtemp(prefix=prefix))

    def add(self, src_path: Path) -> Path:
        dst = self.temp_dir / src_path.name
        # if duplicate name, append counter
        i = 1
        while dst.exists():
            dst = self.temp_dir / f"{src_path.stem}_{i}{src_path.suffix}"
            i += 1
        shutil.copy2(src_path, dst)
        return dst

    def cleanup(self):
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass
