import time
import traceback

from PyQt5.QtCore import pyqtSignal, QThread


class ReqGPT(QThread):
    result = pyqtSignal(str, int)

    def __init__(self, chat_bot, question):
        super().__init__()
        self.chat_bot = chat_bot  # 接收并保存对象的引用
        self.question = question

    def run(self, ):
        # 模拟 I/O 请求（例如，HTTP 请求）
        try:
            use_tokens = self.chat_bot.conversation_with_messages(self.question, self.result)  # 请求数据
            self.result.emit("", use_tokens)  # 发出信号以传递结果
        except Exception as e:
            self.result.emit(str(traceback.print_exc()), 0)
