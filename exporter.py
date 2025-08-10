
from typing import List
from models import Sequence

def build_ffmpeg_command(sequence: Sequence, out_path: str, fps: int = 30) -> List[str]:
    inputs = []
    for track in sequence.tracks:
        for clip in track.clips:
            inputs.extend(["-i", clip.path])
    return ["ffmpeg", "-y", *inputs, "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-shortest", out_path]
