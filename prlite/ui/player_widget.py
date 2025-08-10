from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QSlider, QLabel
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

class PlayerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self._update_slider)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        layout.addWidget(self.video_widget)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self._set_position)
        self.slider.setVisible(False)  # Timeline acts as progress now
        layout.addWidget(self.slider)

        controls = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_btn)

        self.time_label = QLabel("00:00 / 00:00")
        controls.addWidget(self.time_label)

        layout.addLayout(controls)

        self.media_player.stateChanged.connect(self._state_changed)
        self.media_player.durationChanged.connect(self._duration_changed)
        self.media_player.positionChanged.connect(self._position_changed)

    def load(self, path: str):
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        self.media_player.setPosition(0)
        self.media_player.play()
        self.play_btn.setText("Pause")
        self.timer.start()

    def toggle_play(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_btn.setText("Play")
        else:
            self.media_player.play()
            self.play_btn.setText("Pause")

    def _set_position(self, pos):
        self.media_player.setPosition(pos)

    def _update_slider(self):
        # Slider hidden; keep internal updates minimal in case other code relies on values
        self.slider.setMaximum(self.media_player.duration())
        self.slider.setValue(self.media_player.position())

    def _state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setText("Pause")
        else:
            self.play_btn.setText("Play")

    def _duration_changed(self, d):
        self.slider.setMaximum(d)
        self._update_time_label()

    def _position_changed(self, p):
        self.slider.setValue(p)
        self._update_time_label()

    def _update_time_label(self):
        dur = self.media_player.duration() // 1000
        pos = self.media_player.position() // 1000
        def fmt(s):
            m = s // 60
            s2 = s % 60
            return f"{m:02d}:{s2:02d}"
        self.time_label.setText(f"{fmt(pos)} / {fmt(dur)}")
