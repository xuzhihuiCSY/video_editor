import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QHBoxLayout, QSlider, QListWidget, QListWidgetItem, QAbstractItemView
)
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.pos().x()
            total = self.maximum()
            width = self.size().width()
            if width > 0:
                ratio = x / width
                new_val = int(ratio * total)
                self.setValue(new_val)
                self.sliderMoved.emit(new_val)
        super().mousePressEvent(event)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Video Editor")
        self.setGeometry(100, 100, 1000, 600)

        self.setAcceptDrops(True)

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        self.video_list = []
        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_slider)

    def init_ui(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()

        # Left: video player + controls
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        left_layout.addWidget(self.video_widget)

        self.slider = ClickableSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self.set_position)
        left_layout.addWidget(self.slider)

        controls = QHBoxLayout()
        self.play_button = QPushButton("▶ Play")
        self.play_button.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_button)

        left_layout.addLayout(controls)

        # Right: Load button + video list (in vertical layout)
        right_layout = QVBoxLayout()
        self.load_button = QPushButton("Load Video")
        self.load_button.clicked.connect(self.load_video)
        right_layout.addWidget(self.load_button)

        self.list_widget = QListWidget()
        self.list_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_widget.setDragEnabled(True)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.setDropIndicatorShown(True)
        self.list_widget.itemClicked.connect(self.play_selected_video)
        right_layout.addWidget(self.list_widget)

        # Combine left and right
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

        self.setLayout(main_layout)

    # 📂 Load from file dialog
    def load_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_path:
            self.add_video_to_list(file_path)

    # ✅ Shared method for drag-and-load or file-load
    def add_video_to_list(self, file_path):
        self.video_list.append(file_path)
        item = QListWidgetItem(file_path.split("/")[-1])
        item.setData(Qt.UserRole, file_path)
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.list_widget.addItem(item)

    # ▶ Play selected video
    def play_selected_video(self, item):
        file_path = item.data(Qt.UserRole)
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
        self.media_player.setPosition(0)
        self.media_player.play()
        self.play_button.setText("Pause")
        self.timer.start(500)

    def toggle_play(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_button.setText("Play")
        else:
            self.media_player.play()
            self.play_button.setText("Pause")

    def update_slider(self):
        self.slider.setMaximum(self.media_player.duration())
        self.slider.setValue(self.media_player.position())

    def set_position(self, position):
        self.media_player.setPosition(position)

    # ✅ Drag enter support
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(('.mp4', '.avi', '.mov')):
                    event.acceptProposedAction()
                    return
        event.ignore()

    # ✅ Drop support
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.mp4', '.avi', '.mov')):
                self.add_video_to_list(file_path)

    def handle_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            current_row = self.list_widget.currentRow()
            total_items = self.list_widget.count()

            if total_items == 0:
                return  # No videos

            # Move to next video, or loop back to first
            next_row = (current_row + 1) % total_items
            next_item = self.list_widget.item(next_row)

            self.list_widget.setCurrentRow(next_row)
            self.play_selected_video(next_item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
