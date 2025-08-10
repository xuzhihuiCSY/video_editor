
import sys, os, json
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QListWidget, QListWidgetItem,
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QSplitter, QMessageBox, QStyle
)
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget

from models import Clip, Track, Sequence
from timeline import TimelineView
from exporter import build_ffmpeg_command

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XuPR – Mini Editor")
        self.resize(1200, 800)

        self.sequence = Sequence()
        self.media_paths = []
        self.current_ms = 0

        # Timeline play state
        self.timeline_mode = True
        self.play_queue = []
        self.queue_index = 0

        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.video_widget = QVideoWidget(self)
        self.player.setVideoOutput(self.video_widget)

        self.play_btn = QPushButton(self.style().standardIcon(QStyle.SP_MediaPlay), "")
        self.pause_btn = QPushButton(self.style().standardIcon(QStyle.SP_MediaPause), "")
        self.stop_btn = QPushButton(self.style().standardIcon(QStyle.SP_MediaStop), "")
        self.time_lbl = QLabel("00:00.000")
        self.scrub_slider = QSlider(Qt.Horizontal)
        self.scrub_slider.setRange(0, self.sequence.duration_ms)

        self.play_btn.clicked.connect(self.toggle_play_pause)
        self.pause_btn.clicked.connect(self.player.pause)
        self.stop_btn.clicked.connect(self.stop_all)
        self.scrub_slider.valueChanged.connect(self.on_scrub)

        preview_box = QWidget()
        pv = QVBoxLayout(preview_box)
        pv.addWidget(self.video_widget)
        ctrls = QHBoxLayout()
        ctrls.addWidget(self.play_btn)
        ctrls.addWidget(self.pause_btn)
        ctrls.addWidget(self.stop_btn)
        ctrls.addWidget(self.time_lbl)
        ctrls.addWidget(self.scrub_slider, 1)
        pv.addLayout(ctrls)

        self.timeline = TimelineView(self.sequence)
        self.timeline.setMinimumHeight(240)

        center = QWidget()
        cv = QVBoxLayout(center)
        cv.setContentsMargins(0,0,0,0)
        cv.addWidget(preview_box, 2)
        cv.addWidget(self.timeline, 1)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(center)
        self.setCentralWidget(splitter)

        self.media_list = QListWidget()
        media_dock = QDockWidget("Media Bin", self)
        media_dock.setWidget(self.media_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, media_dock)

        self.inspect = QLabel("Inspector\n(select a clip to see properties)")
        self.inspect.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        insp_dock = QDockWidget("Inspector", self)
        insp_wrap = QWidget()
        il = QVBoxLayout(insp_wrap)
        il.addWidget(self.inspect)
        insp_dock.setWidget(insp_wrap)
        self.addDockWidget(Qt.RightDockWidgetArea, insp_dock)

        open_media_act = QAction("Import Media…", self)
        open_media_act.triggered.connect(self.import_media)
        add_to_tl_act = QAction("Add to Timeline", self)
        add_to_tl_act.triggered.connect(self.add_selected_to_timeline)
        zoom_in_act = QAction("Zoom In", self); zoom_in_act.setShortcut("Ctrl++")
        zoom_out_act = QAction("Zoom Out", self); zoom_out_act.setShortcut("Ctrl+-")
        zoom_in_act.triggered.connect(lambda: self.timeline.zoom(1.25))
        zoom_out_act.triggered.connect(lambda: self.timeline.zoom(0.8))

        save_proj_act = QAction("Save Project…", self)
        save_proj_act.triggered.connect(self.save_project)
        open_proj_act = QAction("Open Project…", self)
        open_proj_act.triggered.connect(self.open_project)

        export_act = QAction("Export (stub)…", self)
        export_act.triggered.connect(self.export_stub)

        tb = self.addToolBar("Main")
        for a in [open_media_act, add_to_tl_act, zoom_in_act, zoom_out_act, save_proj_act, open_proj_act, export_act]:
            tb.addAction(a)

        self.media_list.itemSelectionChanged.connect(self.on_media_selected)
        self.player.positionChanged.connect(self.on_player_pos)
        self.player.durationChanged.connect(self.on_player_dur)

        self.tick = QTimer(self)
        self.tick.timeout.connect(self.sync_playhead_from_player)
        self.tick.start(33)

        self.addAction(self._mk_shortcut("Space", self.toggle_play_pause))
        self.addAction(self._mk_shortcut("J", lambda: self.nudge(-1000)))
        self.addAction(self._mk_shortcut("L", lambda: self.nudge(+1000)))
        self.addAction(self._mk_shortcut("K", lambda: self.player.pause()))

    def _mk_shortcut(self, keyseq, fn):
        act = QAction(self)
        act.setShortcut(keyseq)
        act.triggered.connect(fn)
        return act

    # ----- media / project -----
    def import_media(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Import Media", "", "Video Files (*.mp4 *.mov *.mkv *.avi);;All Files (*)")
        for f in files:
            if f not in self.media_paths:
                self.media_paths.append(f)
                item = QListWidgetItem(os.path.basename(f))
                item.setData(Qt.UserRole, f)
                self.media_list.addItem(item)

    def on_media_selected(self):
        # Do NOT load into player; just show details in Inspector
        items = self.media_list.selectedItems()
        if not items:
            self.inspect.setText("Inspector\n(select a clip to see properties)")
            return
        path = items[0].data(Qt.UserRole)
        self.inspect.setText(f"File: {os.path.basename(path)}\nPath: {path}")

    def add_selected_to_timeline(self):
        items = self.media_list.selectedItems()
        if not items:
            QMessageBox.information(self, "No selection", "Select a media item first.")
            return
        path = items[0].data(Qt.UserRole)
        clip = Clip(path=path, start_ms_on_timeline=self.current_ms, track_index=0)
        self.sequence.tracks[0].clips.append(clip)
        self.timeline.redraw_clips_only()

    # ----- timeline playback -----
    def build_play_queue(self):
        # Simple MVP: play V1 track sequentially by start time
        v1 = self.sequence.tracks[0].clips if self.sequence.tracks else []
        return sorted(v1, key=lambda c: c.start_ms_on_timeline)

    def play_timeline_from_current(self):
        self.timeline_mode = True
        self.play_queue = self.build_play_queue()
        if not self.play_queue:
            QMessageBox.information(self, "Timeline empty", "Add clips to V1 to play the timeline.")
            return
        # pick first clip starting at/after current playhead; else start from first
        idx = 0
        for i, c in enumerate(self.play_queue):
            if c.start_ms_on_timeline >= self.current_ms:
                idx = i
                break
        self.queue_index = idx
        self.play_current_queue_item()

    def play_current_queue_item(self):
        if self.queue_index >= len(self.play_queue):
            self.player.stop()
            return
        clip = self.play_queue[self.queue_index]
        self.player.setSource(QUrl.fromLocalFile(clip.path))
        self.player.play()

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            # Always play the timeline, not the selected media
            self.play_timeline_from_current()

    def stop_all(self):
        self.player.stop()
        self.queue_index = 0

    # ----- preview / transport -----
    def on_player_pos(self, ms: int):
        self.current_ms = ms
        self.time_lbl.setText(self._fmt_ms(ms))
        # If we're in timeline mode and close to end, advance to next clip
        dur = self.player.duration()
        if self.timeline_mode and dur > 0 and ms >= max(0, dur - 30):
            # small guard so we don't loop rapidly
            self.queue_index += 1
            self.play_current_queue_item()

        if not self.scrub_slider.isSliderDown():
            self.scrub_slider.blockSignals(True)
            self.scrub_slider.setValue(ms)
            self.scrub_slider.blockSignals(False)

    def on_player_dur(self, ms: int):
        self.scrub_slider.setRange(0, max(ms, self.sequence.duration_ms))

    def sync_playhead_from_player(self):
        self.timeline.set_playhead_ms(self.current_ms)

    def on_scrub(self, ms: int):
        # Only move the playhead visually; actual playback is controlled by timeline
        self.current_ms = ms
        self.timeline.set_playhead_ms(ms)

    def nudge(self, delta_ms: int):
        new_pos = max(0, self.current_ms + delta_ms)
        self.on_scrub(new_pos)

    def export_stub(self):
        out_fn, _ = QFileDialog.getSaveFileName(self, "Export", "output.mp4", "MP4 Video (*.mp4)")
        if not out_fn:
            return
        cmd = build_ffmpeg_command(self.sequence, out_fn)
        QMessageBox.information(self, "Export (stub)", "This is a placeholder command.\n\n" + " ".join(cmd))

    def save_project(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Xu Project (*.xuproj)")
        if not fn: return
        data = {
            "sequence": {
                "name": self.sequence.name,
                "duration_ms": self.sequence.duration_ms,
                "tracks": [
                    {"name": t.name, "clips": [c.__dict__ for c in t.clips]}
                    for t in self.sequence.tracks
                ]
            },
            "media_paths": self.media_paths
        }
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def open_project(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Xu Project (*.xuproj)")
        if not fn: return
        with open(fn, "r", encoding="utf-8") as f:
            data = json.load(f)
        seq = data["sequence"]
        self.sequence = Sequence(name=seq["name"], tracks=[
            Track(t["name"], [Clip(**c) for c in t["clips"]]) for t in seq["tracks"]
        ])
        self.sequence.duration_ms = seq.get("duration_ms", 60_000)
        self.media_paths = data.get("media_paths", [])
        self.timeline.sequence = self.sequence
        self.timeline.redraw_all()
        self.media_list.clear()
        for p in self.media_paths:
            item = QListWidgetItem(os.path.basename(p))
            item.setData(Qt.UserRole, p)
            self.media_list.addItem(item)

    @staticmethod
    def _fmt_ms(ms: int) -> str:
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        return f"{m:02d}:{s:02d}.{ms:03d}"

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
