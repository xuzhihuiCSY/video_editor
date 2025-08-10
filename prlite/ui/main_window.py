import os
from pathlib import Path
from uuid import uuid4

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QMessageBox,
    QMainWindow, QAction, QPushButton
)

from prlite.ui.player_widget import PlayerWidget
from prlite.ui.timeline_widget import TimelineWidget
from prlite.ui.media_bin_widget import MediaBinWidget

from prlite.core.media_store import MediaStore
from prlite.core.project import Project, Clip
from moviepy.editor import VideoFileClip


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PRLite — Timeline as Progress")
        self.resize(1100, 700)

        # Core state
        self.media_store = MediaStore()
        self.project = Project()
        self._clips_by_id = {}
        self._is_playing_timeline = False
        self._timeline_index = 0
        self._timeline_order = []

        self._build_menu()

        # Central layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # Player (left, top)
        self.player = PlayerWidget(self)
        # Connect BOTH signals — these handlers MUST exist
        self.player.media_player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.media_player.positionChanged.connect(self._on_position_changed)
        layout.addWidget(self.player, 3)

        # Timeline (left, bottom)
        self.timeline = TimelineWidget(self)
        self.timeline.orderChanged.connect(self._on_timeline_reordered)
        self.timeline.selectedIdChanged.connect(self._on_timeline_selected)
        layout.addWidget(self.timeline, 1)

        # Controls under timeline
        self.play_timeline_btn = QPushButton("Play Timeline")
        self.play_timeline_btn.clicked.connect(self._play_timeline)
        layout.addWidget(self.play_timeline_btn)

        self.play_from_sel_btn = QPushButton("Play From Selection")
        self.play_from_sel_btn.clicked.connect(self._play_from_selection)
        layout.addWidget(self.play_from_sel_btn)

        # Right column: Media Bin (no playback-on-click)
        right = QVBoxLayout()
        self.media_bin = MediaBinWidget(self)
        # NOTE: we intentionally DO NOT connect clipSelected to preview anymore
        # self.media_bin.clipSelected.connect(self._preview_clip)
        self.media_bin.fileImported.connect(self._import_file)
        self.media_bin.addToTimelineRequested.connect(self._on_add_to_timeline)
        container = QWidget()
        container.setLayout(right)
        right.addWidget(self.media_bin)
        layout.addWidget(container, 1)

    # ==== Menu ====
    def _build_menu(self):
        file_menu = self.menuBar().addMenu("&File")

        new_act = QAction("New Project", self)
        new_act.triggered.connect(self._new_project)
        file_menu.addAction(new_act)

        open_act = QAction("Open Project…", self)
        open_act.triggered.connect(self._open_project)
        file_menu.addAction(open_act)

        save_act = QAction("Save Project", self)
        save_act.triggered.connect(self._save_project)
        file_menu.addAction(save_act)

        saveas_act = QAction("Save Project As…", self)
        saveas_act.triggered.connect(self._save_project_as)
        file_menu.addAction(saveas_act)

    # ==== Import flow ====
    def _import_file(self, src_path: str):
        try:
            src = Path(src_path)
            if not src.exists():
                raise FileNotFoundError(src_path)

            # Safe copy to session temp
            work = self.media_store.add(src)

            # Probe metadata from working copy
            with VideoFileClip(str(work)) as v:
                duration = float(v.duration or 0.0)
                fps = float(v.fps or 0.0)
                w, h = v.size

            clip = Clip(
                id=str(uuid4()),
                name=src.name,
                src_path=str(src.resolve()),
                work_path=str(work.resolve()),
                duration=duration,
                fps=fps,
                width=int(w),
                height=int(h),
                in_point=0.0,
                out_point=duration,
            )

            self.project.add_clip(clip)
            self._clips_by_id[clip.id] = clip

            # Media Bin + auto-add to timeline (timeline is our progress surface)
            self.media_bin.add_item(clip.name, clip.work_path, clip.id)
            self.timeline.add_clip(clip.name, clip.id)
            self._update_timeline_totals()
            self.statusBar().showMessage(f"Imported: {clip.name}", 3000)

        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"Could not import file:\n{e}")

    # Preview a single clip path in player (used by timeline selection)
    def _preview_clip(self, work_path: str):
        self._is_playing_timeline = False  # stop timeline playback if active
        self.player.load(work_path)

    # ==== Project save/load ====
    def _new_project(self):
        self.project = Project()
        self.media_bin.list_widget.clear()
        self.timeline.clear()
        self._clips_by_id = {}
        self._is_playing_timeline = False
        self._timeline_index = 0
        self._timeline_order = []
        self._update_timeline_totals()
        self.statusBar().showMessage("New project created.", 3000)

    def _save_project(self):
        path = getattr(self, "_project_path", None)
        if not path:
            return self._save_project_as()
        self.project.save(Path(path))
        self.statusBar().showMessage(f"Saved: {path}", 3000)

    def _save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project As", "", "PRLite Project (*.prlite.json)")
        if not path:
            return
        if not path.endswith(".prlite.json"):
            path += ".prlite.json"
        self._project_path = path
        self._save_project()

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "PRLite Project (*.prlite.json)")
        if not path:
            return
        try:
            self.project = Project.load(Path(path))
            self.media_bin.list_widget.clear()
            self.timeline.clear()
            self._clips_by_id = {c.id: c for c in self.project.clips}

            # rebuild UI lists
            for c in self.project.clips:
                self.media_bin.add_item(c.name, c.work_path, c.id)
                self.timeline.add_clip(c.name, c.id)

            self._project_path = path
            self._update_timeline_totals()
            self.statusBar().showMessage(f"Opened: {path}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Open Failed", f"Could not open project:\n{e}")

    # ==== Timeline callbacks & helpers ====
    def _on_timeline_reordered(self, ordered_ids):
        """Keep Project.clips in the same order as the Timeline."""
        id_to_clip = {c.id: c for c in self.project.clips}
        new_list = [id_to_clip[cid] for cid in ordered_ids if cid in id_to_clip]
        remaining = [c for c in self.project.clips if c.id not in ordered_ids]
        new_list.extend(remaining)
        self.project.clips = new_list
        self.project.touch()
        self._update_timeline_totals()
        self.statusBar().showMessage("Timeline order updated.", 2000)

    def _on_timeline_selected(self, clip_id: str):
        """Selecting a block previews that clip."""
        clip = self._clips_by_id.get(clip_id)
        if clip:
            self._preview_clip(clip.work_path)

    def _on_add_to_timeline(self, clip_id: str):
        """Media Bin → Add Selected to Timeline (kept for completeness)."""
        clip = self._clips_by_id.get(clip_id)
        if not clip:
            return
        self.timeline.add_clip(clip.name, clip.id)
        self._update_timeline_totals()
        self.statusBar().showMessage(f"Added to timeline: {clip.name}", 2000)

    # ==== Timeline sequential playback ====
    def _play_timeline(self):
        order = self.timeline.get_order_ids()
        if not order:
            return
        self._timeline_order = order
        self._timeline_index = 0
        self._is_playing_timeline = True
        first = self._clips_by_id.get(order[0])
        if first:
            self._preview_clip(first.work_path)

    def _on_media_status_changed(self, status):
        """Advance to next clip when playing the whole timeline."""
        from PyQt5.QtMultimedia import QMediaPlayer
        if not self._is_playing_timeline:
            return
        if status == QMediaPlayer.EndOfMedia:
            self._timeline_index += 1
            if self._timeline_index >= len(self._timeline_order):
                self._is_playing_timeline = False
                return
            next_id = self._timeline_order[self._timeline_index]
            clip = self._clips_by_id.get(next_id)
            if clip:
                self._preview_clip(clip.work_path)

    # ==== Timeline duration helpers + cumulative label ====
    def _compute_timeline_offsets(self, order_ids):
        """Return (offset_by_id, total_seconds) using clip in/out ranges."""
        offset = 0.0
        offsets = {}
        for cid in order_ids:
            clip = self._clips_by_id.get(cid)
            if not clip:
                continue
            dur = max(0.0, (clip.out_point - clip.in_point))
            offsets[cid] = offset
            offset += dur
        return offsets, offset

    def _fmt_mmss(self, seconds: float) -> str:
        s = int(max(0, seconds))
        m = s // 60
        s2 = s % 60
        return f"{m:02d}:{s2:02d}"

    def _on_position_changed(self, pos_ms: int):
        # Only override label & playhead during timeline playback
        if not self._timeline_order or not self._is_playing_timeline:
            return
        if self._timeline_index < 0 or self._timeline_index >= len(self._timeline_order):
            return
        current_id = self._timeline_order[self._timeline_index]
        offsets, total = self._compute_timeline_offsets(self._timeline_order)
        current_offset = offsets.get(current_id, 0.0)
        pos_seconds = (pos_ms or 0) / 1000.0
        timeline_pos = current_offset + pos_seconds
        # update player time label and the timeline's playhead
        self.player.time_label.setText(f"{self._fmt_mmss(timeline_pos)} / {self._fmt_mmss(total)}")
        self.timeline.set_total_seconds(total)
        self.timeline.set_position_seconds(timeline_pos)

    def _play_from_selection(self):
        order = self.timeline.get_order_ids()
        if not order:
            return
        # get selected clip id from the timeline list
        items = self.timeline.list.selectedItems()
        sel_id = items[0].data(0x0100) if items else None  # Qt.UserRole
        if not sel_id:
            return self._play_timeline()
        self._timeline_order = order
        try:
            self._timeline_index = order.index(sel_id)
        except ValueError:
            self._timeline_index = 0
        self._is_playing_timeline = True
        clip = self._clips_by_id.get(self._timeline_order[self._timeline_index])
        if clip:
            self._preview_clip(clip.work_path)

    # ==== Totals ====
    def _update_timeline_totals(self):
        order = self.timeline.get_order_ids()
        total = 0.0
        for cid in order:
            c = self._clips_by_id.get(cid)
            if not c:
                continue
            total += max(0.0, (c.out_point - c.in_point))
        self.timeline.set_total_seconds(total)

    # ==== Cleanup ====
    def closeEvent(self, event):
        try:
            self.media_store.cleanup()
        finally:
            super().closeEvent(event)
