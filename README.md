
# PR-like Video Editor (XuPR)

## Need Action: 

### Core timeline editing

- Trim/extend clip with resize handles (update in_ms/out_ms).

- Move clips with proper snapping (to playhead/edges/seconds).

- Collision & gaps rules (no overlap on same track; optional ripple).

- Select/delete clips; multi-select; drag-drop from Media Bin onto timeline.

- Track headers, add/remove/rename tracks; vertical scrolling & zoom.

### Playback realism

- Honor in/out trims and start times during preview.

- Handle gaps (black/silence) and overlaps (top track wins, or crossfades).

- Optional: simple transitions (crossfade/dip-to-black) for preview.

### Exporter (real)

- Build real FFmpeg graph:

    - Single-track: concat demuxer or trim,setpts,concat.

    - Multi-track: filter_complex with overlay, audio mix, transitions.

- Presets (1080p60, 4K30), progress, cancel, error surfacing.

### Audio

- Separate A-tracks, simple volume per clip, basic mix on export.

- Waveform on audio items (optional later).

### UX polish

- Inspector edit fields (start, in, out, name).

- Undo/redo.

- Thumbnails for clips on timeline (nice-to-have).

- Project settings (FPS, resolution, sample rate).

### Stability

- File-missing handling, relative paths, autosave, tests.

## Setup
Install:
```bash
pip install -r requirements.txt
```

Run:
```bash
python app.py
```
