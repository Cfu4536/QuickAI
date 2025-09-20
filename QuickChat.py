import os
import sys
import psutil
import uuid

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from tools.tools import get_bios_uuid
from window.main_win import main_win


def get_executable_path():
    if getattr(sys, 'frozen', False):
        # 如果是打包成exe的运行环境
        return os.path.dirname(sys.executable)
    else:
        # 如果是在开发环境
        return os.path.dirname(__file__)


def init():
    os.chdir(get_executable_path())
    print("当前工作路径：", os.path.abspath("./"))
    # uuid1 = str(uuid.uuid1())
    # device_id = uuid1.split('-')[2] + uuid1.split('-')[4]  # 设备号
    device_id = get_bios_uuid()
    print("设备id", device_id)
    # with open(os.path.join(user_path, ".quickChart", "uuid.html"), mode='w', encoding='utf-8') as f:
    with open(os.path.join("./src", "uuid.html"), mode='w', encoding='utf-8') as f:
        f.write('''
        <!DOCTYPE html>
<html>
<head>
    <title>激活码</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin-top: 50px;
        }
        .activation-code {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            padding: 20px;
            border: 2px dashed #3498db;
            display: inline-block;
            margin: 20px;
            background-color: #f8f9fa;
        }
    </style>
</head>
<body>
    <h1>您的设备码</h1>
    <div class="activation-code">
        ''' + str(device_id) + '''
        </div>
    <p>请联系作者获取激活码！</p>
</body>
</html>
        ''')
    # 是否已经运行
    Qchat_cnt = 0
    for proc in psutil.process_iter(['pid', 'name']):
        if "QuickChat.exe" == proc.info['name']:
            Qchat_cnt += 1
    if Qchat_cnt > 2:
        sys.exit()


if __name__ == '__main__':
    init()
    # 固定的，PyQt5程序都需要QApplication对象。sys.argv是命令行参数列表，确保程序可以双击运行
    app = QApplication(sys.argv)
    # 初始化窗口
    main_win = main_win(app)
    main_win.resize(1100, 750)  # 设置窗体的宽为800像素，高为600像素
    main_win.setWindowOpacity(0.0)  # 设置窗口透明度0
    main_win.setWindowTitle("QuickAI 2.0")  # 设置窗口标题
    main_win.setWindowIcon(QIcon('src/icon.png'))  # 替换为你的图标文件路径

    # 显示ui界面
    # main_win.show()
    # 创建系统托盘
    main_win.create_tray_icon()
    # 程序运行，sys.exit方法确保程序完整退出。
    sys.exit(app.exec_())
