import hashlib
import json
import os
import subprocess
import sys
import uuid

import markdown2
from PyQt5.QtGui import QFontMetrics
from pygments.formatters.html import HtmlFormatter


def auto_start():
    # 实现开机自启
    # # 启动exe
    if getattr(sys, 'frozen', False):
        # 如果是打包成exe的运行环境
        exe_path = os.path.abspath(r"../bin/auto-start.exe")
        command = f'"{exe_path}" {sys.executable}'

        # 使用 os.popen 执行命令
        process = os.popen(command)
        output = process.read()
        process.close()
        print(output)


def cancel_start():
    if getattr(sys, 'frozen', False):
        # 如果是打包成exe的运行环境
        exe_path = os.path.abspath(r"../bin/auto-start.exe")
        command = f'"{exe_path}"'

        # 使用 os.popen 执行命令
        process = os.popen(command)
        output = process.read()
        process.close()
        print(output)


def hash_encrypt(text, algorithm='sha256'):
    text += "cfu"
    hash_func = hashlib.new(algorithm)
    hash_func.update(text.encode())
    return hash_func.hexdigest()


def get_bios_uuid():
    try:
        cmd = "wmic csproduct get uuid"
        BIOS = subprocess.check_output(cmd, shell=True).decode().split("\n")[1].strip()
        device_id = uuid.uuid5(uuid.NAMESPACE_DNS, BIOS)
        return str(device_id)
    except Exception as e:
        print(e)
    # 获取主板UUID信息 powershell
    try:
        result = subprocess.check_output(
            'powershell -Command "Get-CimInstance -ClassName Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID"',
            shell=True,
            stderr=subprocess.DEVNULL,
            text=True
        )
        uuid_value = result.strip()
        device_id = uuid.uuid5(uuid.NAMESPACE_DNS, uuid_value)
        return str(device_id)
    except Exception as e:
        print(e)


def generate_serial_number():
    bios = get_bios_uuid()
    return hash_encrypt(bios)


def get_welcome_html():
    with open("src/html/welcome.html", mode="r", encoding="utf-8") as r:
        return r.read()


def export_to_md(msg):
    with(open(os.path.abspath("conf/user.json"), mode="r", encoding='utf8')) as f:
        data = json.loads(f.read())
        user_name = data['name']
    str_md = "# conversation\n"
    r = 1
    for data in msg:
        if data['role'] == "system":
            str_md += f"*system: {data['content']}*\n\n"
        elif data['role'] == "user":
            str_md += f"## {r}-{user_name}:\n"
            str_md += f"{data['content']}\n\n"
        elif data['role'] == "assistant":
            str_md += f"## {r}-AI:\n"
            str_md += f"{data['content']}\n\n"
            r += 1
    return str_md


def export_by_pandoc(msg, file_path):
    try:
        # 先保存为临时 .md 文件
        with open("temp.md", mode="w", encoding='utf8') as w:
            w.write(export_to_md(msg))

        # 调用 pandoc 命令行
        subprocess.run([
            './bin/pandoc.exe',
            "temp.md",
            '-o', file_path
        ], check=True)

        os.remove("temp.md")  # 删除临时文件
    except Exception as e:
        print(f"导出失败: {e}")


def get_longest_line_width(text_edit):
    '''文本最小行'''
    # 获取文本内容
    text = text_edit.toPlainText()
    # 按行分割
    lines = text.split('\n')

    if not lines:
        return 0

    # 获取当前字体度量
    font = text_edit.font()
    fm = QFontMetrics(font)

    # 计算每行宽度并找出最小值
    max_width = float(0)
    for line in lines:
        width = fm.width(line)
        if width > max_width:
            max_width = width

    return max_width


def markdown_to_html(markdown_text):
    # 使用 markdown2 渲染 Markdown，并启用代码块高亮（通过 Pygments）
    html = markdown2.markdown(
        markdown_text,
        extras=["fenced-code-blocks"]  # 启用 ``` 代码块支持
    )

    # 可选：自定义 Pygments 高亮样式（默认是 'default' 风格）
    formatter = HtmlFormatter(style="vs")  # 使用 'monokai' 主题。
    css_style = f"<style>{formatter.get_style_defs()}</style>"  # 获取 CSS 样式

    # 将 CSS 插入到 HTML 中
    return f"{css_style}{html}"


if __name__ == '__main__':
    encrypted_str = generate_serial_number()
    print(encrypted_str)
