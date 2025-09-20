import time
import webbrowser
from functools import partial

from PyQt5.QtGui import QIcon, QFont, QKeySequence, QCursor
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu, QAction, QFrame, QLabel, QWidget, \
    QTextEdit, QShortcut, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QEvent, QProcess
from PyQt5 import QtWidgets
from system_hotkey import SystemHotkey

from GPT import GPT3_5_turbo
from UI.main_UI import Ui_MainWindow
from tools.tools import *
from window.notes_viewer import NotesViewer
from window.requestGPT import ReqGPT


class main_win(QMainWindow, Ui_MainWindow):
    # 定义一个热键信号
    sigkeyhot = pyqtSignal(str)

    def __init__(self, app, parent=None):
        super(main_win, self).__init__(parent)
        self.setupUi(self)

        self.app = app
        self.m_flag = False  # 防止拖动窗口闪退
        self.is_response = False  # 是否正在相应

        # 发送问题事件
        self.sent_btn.clicked.connect(self.sent_question)
        self.shortcut = QShortcut(QKeySequence('Ctrl+Return'), self)
        self.shortcut.activated.connect(self.sent_btn.click)

        # 输入框限制
        self.user_input.textChanged.connect(self.limit_text_length)

        # 用户名
        with(open(os.path.abspath("conf/user.json"), mode="r", encoding='utf8')) as f:
            self.user_config = json.loads(f.read())

        # settings
        with (open(os.path.abspath("conf/settings.json"), mode="r", encoding='utf8')) as f:
            self.sys_settings = json.loads(f.read())

        # 模型
        self.chat_bot = GPT3_5_turbo(self.sys_settings)
        self.chat_bot.set_system("AI助手")
        self.allow_conversation_count = 30
        self.max_input_length = 0

        # 系统托盘
        self.init_tray()

        # 对话窗口
        self.widget = QWidget()
        self.widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.vLayout = QtWidgets.QVBoxLayout(self.widget)
        self.scrollArea.setWidget(self.widget)
        self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())

        # 更新数据
        self.update_tokens()
        self.update_model()
        self.update_role("AI助手")

        # 欢迎界面
        self.init_welcome()

        # 置顶，且去掉边框
        # self.setWindowFlags(Qt.WindowStaysOnTopHint | QtCore.Qt.SplashScreen | QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)  # 隐藏关闭按钮

        # 全局快捷键
        self.init_hk()

        # 菜单栏
        self.init_menu()

        # 输入框获取焦点
        self.user_input.setFocus()  # 设置焦点

        # 一定要在最后，点击一下，确保输入框有提示
        self.sent_btn.click()

    def limit_text_length(self):
        text = self.user_input.toPlainText()
        if len(text) > self.max_input_length:
            self.user_input.setPlainText(text[:self.max_input_length])
        self.input_length.setText(f"{len(self.user_input.toPlainText())}/{self.max_input_length}")
        if self.max_input_length - len(self.user_input.toPlainText()) < 400:
            self.input_length.setStyleSheet("color: red;")  # 设置标签的字体颜色为红色
        else:
            self.input_length.setStyleSheet("color: black;")

    def mousePressEvent(self, event):  # 鼠标拖拽窗口移动
        if event.button() == Qt.LeftButton:
            # 判断鼠标点击的位置是否在窗口内部
            self.m_flag = True
            self.m_Position = event.globalPos() - self.pos()  # 获取鼠标相对窗口的位置
            event.accept()
            self.setCursor(QCursor(Qt.OpenHandCursor))  # 更改鼠标图标

    def mouseMoveEvent(self, QMouseEvent):  # 鼠标拖拽窗口移动
        if Qt.LeftButton and self.m_flag:
            self.move(QMouseEvent.globalPos() - self.m_Position)  # 更改窗口位置
            QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):  # 鼠标拖拽窗口移动
        self.m_flag = False
        self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseDoubleClickEvent(self, QMouseEvent):
        self.hide()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            # 检查窗口是否被最小化
            if self.isMinimized():
                print("窗口正在最小化...")
                # 阻止最小化，可以调用：
                # self.showNormal()  # 恢复正常状态
                self.setWindowOpacity(0.0)
                self.hide()

    def create_tray_icon(self):
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(QIcon('src/icon.png'))  # 设置图标
        self.tray_icon.setVisible(True)
        self.tray_icon.setToolTip("Quick Chart")
        # 创建菜单
        self.menu.addAction(self.option_action)
        self.menu.addAction(self.about_action)
        self.menu.addAction(self.exit_action)
        # 将菜单添加到系统托盘图标
        self.tray_icon.setContextMenu(self.menu)
        # 点击显示
        self.tray_icon.activated[QtWidgets.QSystemTrayIcon.ActivationReason].connect(
            partial(self.KeypressEvent, i_str="ishide"))

    def add_conversation_block(self, question):
        # create block
        q_TextEdit = QTextEdit(self.widget)
        self.a_TextEdit = QTextEdit(self.widget)
        q_TextEdit.setStyleSheet(
            "QTextEdit{background-color: #44c0c0c0;border-radius: 20px;border-width: 1px;border-style: hidden;padding: 15px;}"
            "QTextEdit:hover{background-color: #66c0c0c0;border-radius: 20px;border-width: 1px;border-style: hidden;padding: 15px;}")
        self.a_TextEdit.setStyleSheet(
            "QTextEdit{background-color: #44929ff5;border-radius: 20px;border-width: 1px;border-style: hidden;padding: 15px; monospace;}"
            "QTextEdit:hover{background-color: #66929ff5;border-radius: 20px;border-width: 1px;border-style: hidden;padding: 15px;monospace;}")
        q_TextEdit.setFont(QFont('Microsoft YaHei', 12))
        self.a_TextEdit.setFont(QFont('Microsoft YaHei', 12))
        # self.a_TextEdit.setFixedWidth(int(self.scrollArea.width() * 0.8))

        self.ai_label = QLabel(self.widget)
        self.my_label = QLabel(self.widget)
        self.ai_label.setText(self.user_config['AI-name'])
        self.my_label.setText(self.user_config['User-name'])
        self.ai_label.setAlignment(Qt.AlignLeft)
        self.my_label.setAlignment(Qt.AlignRight)

        self.ai_label.setStyleSheet("font-weight: bold;font-size: 20px;border-width: 1px;padding-left: 10px;")
        self.my_label.setStyleSheet("font-weight: bold;font-size: 20px;border-width: 1px;padding-right: 10px;")

        # add block
        self.vLayout.addWidget(self.my_label)
        # QApplication.processEvents()  # 刷新窗口
        self.vLayout.addWidget(q_TextEdit, alignment=Qt.AlignRight)
        # QApplication.processEvents()  # 刷新窗口
        self.vLayout.addWidget(self.ai_label)
        # QApplication.processEvents()  # 刷新窗口
        self.vLayout.addWidget(self.a_TextEdit)

        # set block
        self.a_TextEdit.setReadOnly(True)
        self.a_TextEdit.setMarkdown("思考中...")
        self.a_TextEdit.setFixedHeight(self.a_TextEdit.height() + self.a_TextEdit.verticalScrollBar().maximum())
        QApplication.processEvents()  # 刷新窗口
        q_TextEdit.setReadOnly(True)
        q_TextEdit.setText(question.strip())
        q_TextEdit.setFixedWidth(min(int(self.scrollArea.width() * 0.65), get_longest_line_width(q_TextEdit)) + 60)
        q_TextEdit.setFixedHeight(int(q_TextEdit.document().size().height()) + 32)  # 动态调整高度
        # QApplication.processEvents()  # 刷新窗口

        q_TextEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用垂直滚动条
        q_TextEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        self.a_TextEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用垂直滚动条
        self.a_TextEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        self.scrollArea.setWidget(self.widget)
        self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())
        # QApplication.processEvents()  # 刷新窗口

    def sent_question(self):
        # self.sent_btn.setEnabled(False)  # 禁用发送按钮
        if self.is_response is False:  # 没有响应，发送请求
            self.is_response = True
            self.sent_btn.setText("Stop")
            question = self.user_input.toPlainText()  # 获取问题
            self.user_input.clear()  # 清空输入框
            self.user_input.setFocus()  # 设置焦点
            if question.strip() == "":  # 问题为空
                self.is_response = False
                self.sent_btn.setText("Send")
                return
            self.add_conversation_block(question)
            # 创建线程发送问题
            self.thread = ReqGPT(self.chat_bot, question)
            self.thread.result.connect(self.handle_result)
            self.thread.finished.connect(self.handle_finish)
            self.thread.start()
            # 检查对话次数
            if self.chat_bot.get_conversation_count() >= self.allow_conversation_count:
                self.clear_conversation("对话次数已达上限")
        else:  # 响应中,打断响应
            self.thread.terminate()  # 发送终止信号
            self.thread.wait()  # 等待线程实际退出
            self.is_response = False
            self.sent_btn.setText("Send")

    def handle_result(self, text, use_tokens):
        # 更新主线程
        if use_tokens > 0:
            self.update_tokens(use_tokens)
        if text:
            text = markdown_to_html(text)
            self.a_TextEdit.setHtml(text)
            self.a_TextEdit.setFixedHeight(
                self.a_TextEdit.height() + self.a_TextEdit.verticalScrollBar().maximum())  # 动态更新容器高度
            self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())  # 置低

    def handle_finish(self):
        self.is_response = False  # 结束响应
        self.sent_btn.setText("Send")

    # 热键处理函数
    def KeypressEvent(self, i_str):
        if i_str == "ishide":
            if self.isHidden():
                """淡入动画（从透明到不透明）"""
                self.show()  # 先显示窗口（透明度为0）
                self.showNormal()

                self.animation = QPropertyAnimation(self, b"windowOpacity")
                self.animation.setDuration(500)  # 动画时长（毫秒）
                self.animation.setStartValue(0.0)  # 完全透明
                self.animation.setEndValue(1.0)  # 完全不透明
                self.animation.setEasingCurve(QEasingCurve.OutQuad)  # 平滑曲线
                self.animation.start()
            else:
                """淡出动画（从不透明到透明）"""
                self.animation = QPropertyAnimation(self, b"windowOpacity")
                self.animation.setDuration(200)
                self.animation.setStartValue(1.0)  # 当前透明度
                self.animation.setEndValue(0.0)  # 目标透明度
                self.animation.setEasingCurve(QEasingCurve.OutQuad)

                # 动画结束后隐藏窗口
                self.animation.finished.connect(self.hide)
                self.animation.start()
            self.user_input.setFocus()  # 设置焦点
        elif i_str == "sent" and not self.isHidden():
            self.sent_question()
        elif i_str == "clear" and not self.isHidden():
            self.clear_conversation()

    def update_role(self, name):
        self.label_role.setText("Role: " + name)

    def update_tokens(self, use_tokens=0):
        with(open(os.path.abspath("conf/user.json"), mode="r", encoding='utf8')) as f:
            data = json.loads(f.read())
            self.label_tokens.setText(f"Tokens: {data['use-tokens'] + use_tokens}")
            data['use-tokens'] = data['use-tokens'] + use_tokens
        with(open(os.path.abspath("conf/user.json"), mode="w", encoding='utf8')) as w:
            w.write(json.dumps(data, indent=2))

    def update_model(self, model_name="default"):
        # ["gpt-3.5-turbo-1106", "gpt-4o-mini", "gpt-4o", "spark-lite"]
        if model_name in self.sys_settings['model_list'].keys():
            self.chat_bot.set_model(model_name)
            self.label_model.setText(f"Model:{model_name}")
            self.max_input_length = self.sys_settings['model_list'][model_name]["max_input_length"]
            self.allow_conversation_count = self.sys_settings['model_list'][model_name]["allow_conversation_count"]
            with(open(os.path.abspath("conf/user.json"), mode="r", encoding='utf8')) as f:
                data = json.loads(f.read())
                data['default-model'] = model_name
            with(open(os.path.abspath("conf/user.json"), mode="w", encoding='utf8')) as w:
                w.write(json.dumps(data, indent=2))
        else:  # default
            with(open(os.path.abspath("conf/user.json"), mode="r", encoding='utf8')) as f:
                data = json.loads(f.read())
                model_name = data['default-model']
                self.update_model(model_name)
        self.limit_text_length()

    # 热键信号发送函数(将外部信号，转化成qt信号)
    def sendkeyevent(self, i_str):
        self.sigkeyhot.emit(i_str)

    def clichOption(self):
        pass

    def clichAbout(self):
        self.sentMessage("关于", "Quick AI-v1.3\n@cfu\n")

    def clickDestory(self):
        self.app.quit()

    def sentMessage(self, title, content):
        self.tray_icon.showMessage(title, content, QSystemTrayIcon.Information, 1000)

    def clear_conversation(self, info="已清空对话"):
        self.chat_bot.clear_conversation()
        self.clear_label = QLabel(self.widget)
        self.clear_label.setText(f"- {info} -")
        self.clear_label.setStyleSheet("")
        self.clear_label.setAlignment(Qt.AlignCenter)
        self.clear_label.setFont(QFont('Microsoft YaHei UI Light', 8))
        line = QFrame()
        line.setFrameShape(QFrame.HLine)  # 设置形状为水平线
        line.setFrameShadow(QFrame.Sunken)  # 设置阴影样式

        self.vLayout.addWidget(self.clear_label)
        self.vLayout.addWidget(line)
        self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())  # 置低

    def new_conversation(self):
        self.clear_conversation()

    def save_conversation(self, type):
        fileName, fileType = QtWidgets.QFileDialog.getSaveFileName(self, "文件保存", os.path.abspath(
            os.path.join("myDialogs", f"{int(time.time())}")) + type, type)

        print(fileName)
        print(fileType)
        return fileName, fileType

    def con_export_md(self):
        fileName, fileType = self.save_conversation(".md")
        if fileName == "":
            return
        elif fileName.endswith(".md"):
            self.chat_bot.export_conversation_to_md(fileName)
        else:
            self.chat_bot.export_conversation_to_md(fileName + ".md")

    def con_export_html(self):
        fileName, fileType = self.save_conversation(".html")
        if fileName == "":
            return
        if fileName.endswith(".html"):
            self.chat_bot.export_conversation_to_html(fileName)
        else:
            self.chat_bot.export_conversation_to_html(fileName + ".html")

    def con_export_doc(self):
        fileName, fileType = self.save_conversation(".docx")
        if fileName == "":
            return
        elif fileName.endswith(".docx"):
            self.chat_bot.export_conversation_to_doc(fileName)
        else:
            self.chat_bot.export_conversation_to_doc(fileName + ".docx")

    def con_export_txt(self):
        fileName, fileType = self.save_conversation(".txt")
        if fileName == "":
            return
        elif fileName.endswith(".txt"):
            self.chat_bot.export_conversation_to_txt(fileName)
        else:
            self.chat_bot.export_conversation_to_txt(fileName + ".txt")

    def con_export_pdf(self):
        fileName, fileType = self.save_conversation(".pdf")
        if fileName == "":
            return
        elif fileName.endswith(".pdf"):
            self.chat_bot.export_conversation_to_pdf(fileName)
        else:
            self.chat_bot.export_conversation_to_pdf(fileName + ".pdf")

    def visit_URL(self, url):
        print(url)
        webbrowser.open_new_tab(url)

    def get_role(self, name):
        self.chat_bot.set_system(name)
        self.clear_conversation(info="已切换角色")
        self.update_role(name)

    def open_note(self, note_path):
        self.hide()
        self.viewer = NotesViewer(note_path, parent=self)
        self.viewer.show()

    def init_menu(self):
        # 开始
        self.action_md.triggered.connect(self.con_export_md)
        self.action_html.triggered.connect(self.con_export_html)
        self.action_docx.triggered.connect(self.con_export_doc)
        self.action_txt.triggered.connect(self.con_export_txt)
        self.action_pdf.triggered.connect(self.con_export_pdf)
        self.actionexport_folder.triggered.connect(partial(self.default_open_file, "./myDialogs"))
        self.new_2.triggered.connect(self.new_conversation)
        self.actiongettokens.triggered.connect(
            partial(self.visit_URL, os.path.join("src", "uuid.html")))
        self.actionclear_screen.triggered.connect(self.clear_screen)
        self.actionchongqi.triggered.connect(self.restart)
        self.actionexit_app.triggered.connect(self.exit_app)

        # 效率
        for category, url_list in self.sys_settings['collection'].items():
            ct_menu = QtWidgets.QMenu(self.menubar)
            ct_menu.setTitle(category)
            for url_item in url_list:
                ct_menu.addAction(
                    QtWidgets.QAction(url_item['name'], self, triggered=partial(self.visit_URL, url_item['url'])))
            self.menu_5.addMenu(ct_menu)

        # help
        self.actionhelp.triggered.connect(partial(self.visit_URL, f"{os.path.abspath('./src/html/help.html')}"))
        self.actionupdate.triggered.connect(partial(self.visit_URL, os.path.abspath('./src/html/download.html')))
        self.actiondonation.triggered.connect(partial(self.visit_URL, f"{os.path.abspath('./src/html/donate.html')}"))
        self.actionopen_address.triggered.connect(partial(self.visit_URL, 'https://github.com/Cfu4536/quickAI'))
        # 开机自启
        self.actionstart.triggered.connect(self.start_up)
        self.actioncancelstartup.triggered.connect(self.cancel_start)

        # 设置
        self.actionsettings.triggered.connect(partial(self.default_open_file, 'conf/settings.json'))
        self.actiontheme.triggered.connect(partial(self.default_open_file, 'conf/theme.json'))
        # 角色扮演
        self.actionzhushou.triggered.connect(partial(self.get_role, "AI助手"))
        self.actionzhongyiying.triggered.connect(partial(self.get_role, "中译英"))
        self.actionyingyizhong.triggered.connect(partial(self.get_role, "英译中"))
        self.actionlunwenrunse.triggered.connect(partial(self.get_role, "论文润色"))
        self.actionnvninvyou.triggered.connect(partial(self.get_role, "虚拟女友"))
        self.actionxuninanyou.triggered.connect(partial(self.get_role, "虚拟男友"))
        self.actionzhanan.triggered.connect(partial(self.get_role, "渣男"))
        self.actionpython.triggered.connect(partial(self.get_role, "python专家"))
        self.actionjava.triggered.connect(partial(self.get_role, "java专家"))
        self.actionc_zhuanjai.triggered.connect(partial(self.get_role, "c++专家"))
        self.actionwebqianduan.triggered.connect(partial(self.get_role, "web前端专家"))
        self.actionwebhouduan.triggered.connect(partial(self.get_role, "web后端专家"))
        self.actionlinux.triggered.connect(partial(self.get_role, "linux高手"))
        self.actiondeeplearning.triggered.connect(partial(self.get_role, "深度学习专家"))
        self.actionmachine.triggered.connect(partial(self.get_role, "机器学习专家"))
        for role_name, role_info in self.sys_settings["role_list"].items():
            self.action_role = QtWidgets.QAction(self)
            self.action_role.setText(role_name)
            self.action_role.triggered.connect(partial(self.get_role, role_name))
            self.menu_11.addAction(self.action_role)

        # 模型切换["gpt-3.5-turbo-1106", "gpt-4o-mini", "gpt-4o"]
        for model_name, model_info in self.sys_settings["model_list"].items():
            action_model = QtWidgets.QAction(self)
            action_model.setText(model_name)
            action_model.triggered.connect(partial(self.update_model, model_name))
            self.menu_14.addAction(action_model)

        # 笔记
        for file_name in os.listdir(r"./src/notes"):
            action_note = QtWidgets.QAction(self)
            action_note.setText(file_name.split(".")[0])
            action_note.triggered.connect(partial(self.open_note, f"./src/notes/{file_name}"))
            self.menu_notes.addAction(action_note)

    def init_hk(self):
        # 2. 设置我们的自定义热键响应函数
        self.sigkeyhot.connect(self.KeypressEvent)
        # 3. 初始化两个热键
        self.hk_hide, self.hk_sent, self.hk_clear = SystemHotkey(), SystemHotkey(), SystemHotkey()
        # 4. 绑定快捷键和对应的信号发送函数
        self.hk_hide.register(('alt', 'w'), callback=lambda x: self.sendkeyevent("ishide"))
        self.hk_sent.register(('alt', 'q'), callback=lambda x: self.sendkeyevent("sent"))
        self.hk_clear.register(('alt', 'c'), callback=lambda x: self.sendkeyevent("clear"))

    def init_tray(self):
        '''
        设置系统托盘右键
        :return:
        '''
        self.tray_icon = QSystemTrayIcon()
        self.menu = QMenu()
        self.option_action = QAction('首选项', triggered=self.clichOption)
        self.about_action = QAction('关于', triggered=self.clichAbout)
        self.exit_action = QAction('退出', triggered=self.clickDestory)

    def init_welcome(self):
        # 设置欢饮界面
        self.welcome_TextEdit = QTextEdit(self.widget)
        self.welcome_TextEdit.setStyleSheet(
            "QTextEdit{border-radius: 8px;border-width: 1px;border-style: hidden;}"
        )
        self.vLayout.addWidget(self.welcome_TextEdit)
        self.welcome_TextEdit.setHtml(get_welcome_html())
        self.welcome_TextEdit.setFixedHeight(self.scrollArea.maximumHeight())
        self.welcome_TextEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用垂直滚动条
        self.welcome_TextEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        self.welcome_TextEdit.setReadOnly(True)

        # QApplication.processEvents()  # 刷新窗口

    def start_up(self):
        auto_start()

    def cancel_start(self):
        cancel_start()

    def default_open_file(self, path):
        os.startfile(os.path.abspath(path))

    def clear_screen(self):
        # 反向遍历，避免删除时索引变化问题
        for i in reversed(range(self.vLayout.count())):
            item = self.vLayout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()  # 安全删除widget
            elif item.layout():
                # 如果是子layout，递归清除
                self.clear_layout(item.layout())
                item.layout().deleteLater()
        self.init_welcome()

    def exit_app(self):
        reply = QMessageBox.question(
            self,
            '确认退出',
            '确定要退出程序吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.clickDestory()  # 触发点击退出按钮的槽函数

    def restart(self):
        reply = QMessageBox.question(
            self,
            '确认重启',
            '确定要重启吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 如果是直接运行的脚本
            if not getattr(sys, 'frozen', False):
                # 获取当前脚本的完整路径（包括文件名）
                script_file = os.path.abspath(__file__)
            else:
                # 如果是打包后的exe
                script_file = sys.executable

            self.app.quit()
            print(script_file)
            if script_file.endswith(".exe"):
                os.startfile(script_file)
            sys.exit()
