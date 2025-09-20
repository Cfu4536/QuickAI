from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 创建文本编辑框
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText("按住Ctrl键并滚动鼠标滚轮可以调整文本大小\n"
                                    "这是直接在MainWindow中实现的方案，无需继承QTextEdit")

        # 设置中央部件
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # 安装事件过滤器
        self.text_edit.installEventFilter(self)

        self.setWindowTitle("Ctrl+滚轮调整文本大小")
        self.resize(600, 400)

    def eventFilter(self, obj, event):
        # 只处理文本编辑框的滚轮事件
        if obj == self.text_edit and event.type() == event.Wheel:
            # 检查是否按下了Ctrl键
            if event.modifiers() == Qt.ControlModifier:
                # 根据滚轮方向调整大小
                if event.angleDelta().y() > 0:
                    self.text_edit.zoomIn()  # 向上滚动，放大
                else:
                    self.text_edit.zoomOut()  # 向下滚动，缩小
                return True  # 事件已处理，不再传递

        # 其他事件交给默认处理
        return super().eventFilter(obj, event)


app = QApplication([])
window = MainWindow()
window.show()
app.exec_()