try:
    import win32gui as w
    import win32con as wc
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from typing import *
    from PyQt5.QtCore import Qt
except ImportError as e:
    import ctypes
    ctypes.windll.user32.MessageBoxW(None, f"{e}", u"Error", 0)
    quit()


class App(QWidget):
    def __init__(self, parent=None):
        super(App, self).__init__(parent)
        main_layout = QVBoxLayout()
        self.processes: List[int] = []
        # Top
        self._top()
        main_layout.addLayout(self.top_layout)
        # List
        self._list()
        main_layout.addWidget(self.list_tree)
        # Looks
        self.setLayout(main_layout)
        QApplication.setStyle("Fusion")
        self.setWindowTitle("Fullscreener")
        #
        self._refresh()

    def _get_selected(self) -> int:
        try:
            hwnd = self.list_tree.currentItem().text(2)
            return int(hwnd)
        except Exception as e:
            print(e)

    def focus(self):
        try:
            hwnd = self._get_selected()
            w.SetForegroundWindow(hwnd)
            w.ShowWindow(hwnd, wc.SW_SHOWNORMAL)
        except Exception as e:
            print(e)

    def set_fullscreen_windowed(self):
        try:
            hwnd = self._get_selected()
            w.SetWindowLong(hwnd, wc.GWL_STYLE, 0)  # Set style to 0
            w.ShowWindow(hwnd, wc.SW_SHOWNORMAL)
            w.SetWindowPos(hwnd, 0, 0, 0, 1920, 1080, 0)
        except Exception as e:
            print(e)

    def _top(self):
        self.top_layout = QHBoxLayout()

        button_focus = QPushButton("Focus")
        button_focus.clicked.connect(self.focus)

        button_refresh = QPushButton("Refresh")
        button_refresh.clicked.connect(self._refresh)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.textChanged.connect(self._refresh)

        button_fullscreen = QPushButton("Fullscreen Windowed")
        button_fullscreen.clicked.connect(self.set_fullscreen_windowed)

        self.top_layout.addWidget(button_focus)
        self.top_layout.addWidget(button_refresh)
        self.top_layout.addWidget(self.search_bar)
        self.top_layout.addWidget(button_fullscreen)

    def _list(self):
        self.list_tree = QTreeWidget()
        headers = ("Window name", "Class name", "hwnd")
        self.list_tree.setColumnCount(len(headers))
        self.list_tree.setHeaderLabels(headers)
        self.list_tree.setSortingEnabled(True)
        self.list_tree.sortByColumn(0, Qt.AscendingOrder)
        self.list_tree.setRootIsDecorated(False)
        self.list_tree.setColumnWidth(0, 200)
        self.list_tree.setColumnWidth(2, 50)
        self.list_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def _refresh(self):
        self.processes = []
        self.list_tree.clear()
        w.EnumWindows(lambda x, _: self.processes.append(x), None)

        def filter_function(hwnd: int) -> bool:
            window_name = w.GetWindowText(hwnd)
            class_name = w.GetClassName(hwnd)
            if window_name == "":
                return False
            if class_name == "IME":
                return False
            if class_name == "MSCTFIME UI":
                return False

            # Searching
            if self.search_bar.text().lower() not in f"{window_name} {class_name}".lower():
                return False
            return True

        self.processes = [*filter(filter_function, self.processes)]

        # Populate list
        for hwnd in self.processes:
            item = QTreeWidgetItem(self.list_tree)
            item.setText(0, f"{w.GetWindowText(hwnd)}")
            item.setText(1, f"{w.GetClassName(hwnd)}")
            item.setText(2, f"{hwnd}")


if __name__ == '__main__':
    app = QApplication([])
    console = App()
    console.show()
    app.exec_()
