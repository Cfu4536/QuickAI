import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QMenu, QMessageBox

from UI.note_viewer import Ui_NoteViewer
from tools.tools import markdown_to_html


class NotesViewer(QMainWindow, Ui_NoteViewer):
    def __init__(self, note_path, parent=None):
        super(NotesViewer, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("记事本")

        self.note_path = note_path
        self.parent_window = parent  # 保存父窗口引用
        self.content = ""
        self.is_content_changed = False
        self.view = "read"
        self.show_note()

        # 创建菜单
        self.context_menu = QMenu(self)
        self.copy_action = self.context_menu.addAction("复制")
        self.paste_action = self.context_menu.addAction("粘贴")
        self.change_view_action = self.context_menu.addAction("切换编辑/阅读视图")
        self.context_menu.addSeparator()
        # 连接信号
        self.copy_action.triggered.connect(self.notes_textEdit.copy)
        self.paste_action.triggered.connect(self.notes_textEdit.paste)
        self.change_view_action.triggered.connect(self.change_view)
        # 设置上下文菜单策略
        self.notes_textEdit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.notes_textEdit.customContextMenuRequested.connect(self.show_context_menu)

        # # 安装事件过滤器
        self.notes_textEdit.installEventFilter(self)

        # 连接textChanged信号
        self.notes_textEdit.textChanged.connect(self.on_text_changed)

    def show_context_menu(self, pos):
        # 根据当前状态启用/禁用菜单项
        self.copy_action.setEnabled(self.notes_textEdit.textCursor().hasSelection())
        self.paste_action.setEnabled(self.notes_textEdit.canPaste())

        # 显示菜单
        self.context_menu.exec_(self.notes_textEdit.mapToGlobal(pos))

    def eventFilter(self, obj, event):
        # 只处理文本编辑框的滚轮事件
        if obj == self.notes_textEdit and event.type() == event.Wheel:
            # 检查是否按下了Ctrl键
            if event.modifiers() == Qt.ControlModifier:
                # 根据滚轮方向调整大小
                if event.angleDelta().y() > 0:
                    self.notes_textEdit.zoomIn()  # 向上滚动，放大
                else:
                    self.notes_textEdit.zoomOut()  # 向下滚动，缩小
                event.accept()  # 明确接受事件，阻止进一步传播
                return True  # 事件已处理，不再传递

        # 其他事件交给默认处理
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        # 如果内容未更改，直接关闭窗口
        if not self.is_content_changed:
            self.parent_window.show()
            event.accept()  # 接受关闭事件
            return
        # 创建确认对话框
        reply = QMessageBox.question(
            self,
            '退出',
            '确定要保存当前内容吗？',
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                with open(self.note_path, mode='w', encoding='utf-8') as f:
                    f.write(self.content)
            except:
                # 警告框
                QMessageBox.warning(self, '警告', '保存失败！')
                return
            self.parent_window.show()
            event.accept()  # 接受关闭事件
        elif reply == QMessageBox.No:
            self.parent_window.show()
            event.accept()  # 接受关闭事件
        else:
            event.ignore()

    def on_text_changed(self):
        if self.view == "edit":
            self.content = self.notes_textEdit.toPlainText()
            self.is_content_changed = True
            print("内容已更新")

    def show_note(self):
        '''
        启动时，显示笔记内容
        '''
        try:
            with open(self.note_path, mode='r', encoding='utf-8') as f:
                self.content = f.read()
                text = markdown_to_html(self.content)
                self.notes_textEdit.setHtml(text)
                self.notes_textEdit.setReadOnly(True)
                self.label_info.setText("视图模式：仅阅读" + " | " + "已打开的笔记：" + os.path.basename(self.note_path))
        except  Exception as e:
            QMessageBox.warning(self, '警告', '读取文件失败！')
            self.parent_window.show()
            self.close()

    def change_view(self):
        '''
        切换视图
        '''
        if self.view == "read":
            self.view = "edit"
            self.notes_textEdit.setPlainText(self.content)
            self.notes_textEdit.setReadOnly(False)
            self.label_info.setText("视图模式：可编辑" + " | " + "已打开的笔记：" + os.path.basename(self.note_path))
        else:
            self.view = "read"
            text = markdown_to_html(self.content)
            self.notes_textEdit.setHtml(text)
            self.notes_textEdit.setReadOnly(True)
            self.label_info.setText("视图模式：仅阅读" + " | " + "已打开的笔记：" + os.path.basename(self.note_path))
