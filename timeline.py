
import os
from typing import List
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QBrush, QPen
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem
from models import Sequence, Clip

class ClipItem(QGraphicsRectItem):
    def __init__(self, clip: Clip, px_per_sec: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clip = clip
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemSendsScenePositionChanges, True)
        self.setBrush(QBrush(Qt.darkCyan))
        self.setPen(QPen(Qt.black))
        self.px_per_sec = px_per_sec
        self.setToolTip(os.path.basename(clip.path))

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionChange:
            new_pos = value
            snapped_x = round(new_pos.x() / (self.px_per_sec/100)) * (self.px_per_sec/100)
            track_height = 40
            snapped_y = round(new_pos.y() / track_height) * track_height
            return QPointF(max(0, snapped_x), max(0, snapped_y))
        return super().itemChange(change, value)

class TimelineView(QGraphicsView):
    def __init__(self, sequence: Sequence):
        super().__init__()
        self.sequence = sequence
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(self.renderHints())
        self.setMouseTracking(True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setBackgroundBrush(QBrush(Qt.darkGray))
        self.px_per_sec = 100.0
        self.track_height = 40
        self.clip_items: List[ClipItem] = []
        self.scrubber = self.scene.addLine(0, 0, 0, 1000, QPen(Qt.red, 2))
        self.redraw_grid()

    def timeline_to_x(self, ms: int) -> float:
        return (ms / 1000.0) * self.px_per_sec

    def x_to_timeline_ms(self, x: float) -> int:
        return int((x / self.px_per_sec) * 1000)

    def set_playhead_ms(self, ms: int):
        x = self.timeline_to_x(ms)
        self.scrubber.setLine(x, 0, x, 1000)

    def zoom(self, factor: float):
        self.px_per_sec = max(10.0, min(1000.0, self.px_per_sec * factor))
        self.redraw_all()

    def redraw_grid(self):
        self.scene.clear()
        self.clip_items.clear()
        total_height = self.track_height * max(3, len(self.sequence.tracks))
        total_width = self.timeline_to_x(self.sequence.duration_ms)
        self.scene.setSceneRect(0, 0, max(total_width, 2000), total_height)
        for i in range(max(3, len(self.sequence.tracks))):
            band = self.scene.addRect(QRectF(0, i*self.track_height, total_width, self.track_height),
                                      QPen(Qt.NoPen),
                                      QBrush(Qt.gray if i % 2 == 0 else Qt.lightGray))
            band.setZValue(-2)
        secs = int(self.sequence.duration_ms / 1000) + 1
        for s in range(secs):
            x = self.timeline_to_x(s * 1000)
            line = self.scene.addLine(x, 0, x, self.track_height*len(self.sequence.tracks), QPen(Qt.black, 0.5))
            line.setZValue(-1)
            lbl = self.scene.addText(f"{s:02d}s")
            lbl.setDefaultTextColor(Qt.white)
            lbl.setPos(x+2, 2)
            lbl.setZValue(-1)
        self.scrubber = self.scene.addLine(0, 0, 0, self.track_height*len(self.sequence.tracks), QPen(Qt.red, 2))

    def add_clip(self, clip: Clip):
        dur_ms = clip.out_ms - clip.in_ms if clip.out_ms else 5000
        x = self.timeline_to_x(clip.start_ms_on_timeline)
        y = clip.track_index * self.track_height
        w = self.timeline_to_x(dur_ms)
        h = self.track_height - 6
        item = ClipItem(clip, self.px_per_sec)
        item.setRect(QRectF(x, y+3, w, h))
        self.scene.addItem(item)
        self.clip_items.append(item)

    def redraw_clips_only(self):
        for item in list(self.clip_items):
            self.scene.removeItem(item)
        self.clip_items.clear()
        for t_index, track in enumerate(self.sequence.tracks):
            for clip in track.clips:
                self.add_clip(clip)

    def redraw_all(self):
        self.redraw_grid()
        self.redraw_clips_only()
