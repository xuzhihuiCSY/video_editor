from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QSlider

class TimelineWidget(QWidget):
    """
    Minimal timeline: a single horizontal track of clip blocks.
    - Drag to reorder
    - Click to select
    Emits:
      orderChanged(list_of_ids)
      selectedIdChanged(clip_id or None)
    """
    orderChanged = pyqtSignal(list)
    selectedIdChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.label = QLabel("Timeline (drag to reorder)")
        layout.addWidget(self.label)

        # Thin read-only playhead bar (acts like a progress bar)
        self.playhead = QSlider(Qt.Horizontal)
        self.playhead.setEnabled(False)
        self.playhead.setFixedHeight(10)
        layout.addWidget(self.playhead)

        self.list = QListWidget()
        self.list.setFlow(QListWidget.LeftToRight)
        self.list.setWrapping(False)
        self.list.setDragEnabled(True)
        self.list.setAcceptDrops(True)
        self.list.setDefaultDropAction(Qt.MoveAction)
        self.list.setDragDropMode(self.list.InternalMove)
        self.list.setSelectionMode(self.list.SingleSelection)
        self.list.setUniformItemSizes(True)
        self.list.model().rowsMoved.connect(self._on_rows_moved)
        self.list.itemSelectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self.list)

    def clear(self):
        self.list.clear()

    def set_clips(self, items):
        """items: list of (display_name, clip_id) in order"""
        self.clear()
        for name, cid in items:
            self.add_clip(name, cid)

    def add_clip(self, display_name, clip_id):
        it = QListWidgetItem(display_name)
        it.setData(Qt.UserRole, clip_id)
        it.setTextAlignment(Qt.AlignCenter)
        # Fixed size for timeline blocks
        it.setSizeHint(QtCore.QSize(120, 50))
        self.list.addItem(it)

    def get_order_ids(self):
        return self._current_order_ids()

    def _current_order_ids(self):
        ids = []
        for i in range(self.list.count()):
            it = self.list.item(i)
            cid = it.data(Qt.UserRole)
            ids.append(cid)
        return ids

    def _on_rows_moved(self, *args, **kwargs):
        self.orderChanged.emit(self._current_order_ids())

    def _on_selection_changed(self):
        items = self.list.selectedItems()
        if not items:
            return
        it = items[0]
        cid = it.data(Qt.UserRole)
        if cid:
            self.selectedIdChanged.emit(cid)


    # ---- Playhead API ----
    def set_total_seconds(self, total: float):
        self.playhead.setMaximum(int(max(1, total * 1000)))  # ms

    def set_position_seconds(self, pos: float):
        self.playhead.setValue(int(max(0, pos * 1000)))
