
# PR-like Video Editor (XuPR) – v6

Changes requested:
- **Media Bin no longer plays** the selected file. It only shows info in the Inspector.
- **Play button now plays the entire timeline** (MVP behavior: plays clips on V1 sequentially by start time).

Notes:
- Scrubbing moves the playhead visually; playback always comes from the timeline queue.
- This MVP ignores gaps/overlaps and clip in/out trims for preview.

Install:
```bash
pip install -r requirements.txt
```

Run:
```bash
python app.py
```
