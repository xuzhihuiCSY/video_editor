from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QFileDialog
)

class MediaBinWidget(QWidget):
    # Signals
    clipSelected = pyqtSignal(str)            # (unused now; playback from bin disabled)
    fileImported = pyqtSignal(str)            # emits src_path to import/copy
    addToTimelineRequested = pyqtSignal(str)  # emits clip_id to add to timeline

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.setAcceptDrops(True)

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Import button
        self.import_btn = QPushButton("Import Media…")
        self.import_btn.clicked.connect(self._on_import_clicked)
        layout.addWidget(self.import_btn)

        # Add to Timeline button
        self.add_btn = QPushButton("Add Selected to Timeline")
        self.add_btn.clicked.connect(self._on_add_selected)
        layout.addWidget(self.add_btn)

        # Media list (click does NOT play anymore)
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

    # ---- Public API ----
    def add_item(self, display_name: str, work_path: str, clip_id: str):
        """Add a media item to the bin."""
        item = QListWidgetItem(display_name)
        item.setData(Qt.UserRole, work_path)      # for preview (currently disabled)
        item.setData(Qt.UserRole + 1, clip_id)    # for timeline add
        self.list_widget.addItem(item)

    # ---- UI Handlers ----
    def _on_import_clicked(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if path:
            self.fileImported.emit(path)

    def _on_item_clicked(self, item: QListWidgetItem):
        # Playback from Media Bin is intentionally disabled.
        # If you ever want to enable preview-on-click again:
        # work_path = item.data(Qt.UserRole)
        # if work_path:
        #     self.clipSelected.emit(work_path)
        pass

    def _on_add_selected(self):
        items = self.list_widget.selectedItems()
        if not items:
            return
        it = items[0]
        clip_id = it.data(Qt.UserRole + 1)
        if clip_id:
            self.addToTimelineRequested.emit(clip_id)

    # ---- Drag & Drop ----
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        for u in urls:
            p = u.toLocalFile()
            if p:
                self.fileImported.emit(p)
