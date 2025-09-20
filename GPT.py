import hashlib
import json
import os
import subprocess
import tempfile
import time
import uuid

import requests
from PyQt5.QtWidgets import QApplication
from tools import *
from openai import OpenAI

from tools.tools import *


class GPT3_5_turbo():
    def __init__(self, settings: dict):
        self.messages = []
        self.conversation_count = 0  # 对话轮数
        self.tocken_count = 0
        self.key_index = 0
        self.settings = settings
        self.model = "gpt-3.5-turbo-1106"
        self.role = "AI助手"
        self.client = OpenAI(
            # defaults to os.environ.get("OPENAI_API_KEY")
            api_key=self.settings['model_list'][self.model]['api_key'][self.key_index],
            base_url=self.settings['model_list'][self.model]['url']
        )

    def call_with_stream(self, messages, result):
        print(self.model)
        role = 'assistant'
        full_content = ''  # with incrementally we need to merge output.
        if self.model == "spark-lite":
            try:
                api_key = self.settings['model_list'][self.model]['api_key'][0]
                url = self.settings['model_list'][self.model]['url']
                data = {
                    "model": "lite",  # 指定请求的模型
                    "messages": messages,
                    "stream": True
                }
                header = {
                    "Authorization": "Bearer " + api_key  # 注意此处替换自己的APIPassword
                }
                response = requests.post(url, headers=header, json=data, stream=True)

                # 流式响应解析示例
                response.encoding = "utf-8"
                for line in response.iter_lines(decode_unicode="utf-8"):
                    try:
                        line = line[5:].strip()
                        line = json.loads(str(line))
                        if line["choices"][0]["delta"]["content"]:
                            full_content += line["choices"][0]["delta"]["content"]
                            self.tocken_count += 2
                            print(line["choices"][0]["delta"]["content"], end="")
                            result.emit(full_content, 0)
                        else:
                            print("over")
                            break
                    except:
                        continue
                return True, role, full_content
            except:
                return False, role, full_content
        else:  # 非讯飞星火，调用openai的sdk
            try:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    temperature=1,  # number 可选 默认 1;数字0~2之间数字越大，答案越随机，开放，比如1.8数字越小，答案越固定，聚焦，比如0.2建议不要同时和top_p修改

                )
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        full_content += chunk.choices[0].delta.content
                        self.tocken_count += 2
                        print(chunk.choices[0].delta.content, end="")
                        result.emit(full_content, 0)
                        # TextEdit.setMarkdown(full_content)
                        # TextEdit.setFixedHeight(TextEdit.height() + TextEdit.verticalScrollBar().maximum())  # 动态更新容器高度
                        # QApplication.processEvents()  # 刷新窗口
                        # scrollArea.verticalScrollBar().setValue(scrollArea.verticalScrollBar().maximum())  # 置低
                    else:
                        # TextEdit.setFixedHeight(TextEdit.height() + TextEdit.verticalScrollBar().maximum())  # 动态更新容器高度
                        # QApplication.processEvents()  # 刷新窗口
                        # scrollArea.verticalScrollBar().setValue(scrollArea.verticalScrollBar().maximum())  # 置低
                        print("over")
                        break
                return True, role, full_content
            except:
                return False, role, full_content

    def check_auth(self):
        uuid1 = str(uuid.uuid1())
        device_id = uuid1.split('-')[2] + uuid1.split('-')[4]  # 设备号
        # 创建md5对象
        # hash_md5 = hashlib.md5()
        # hash_md5.update(device_id.encode('utf-8'))
        # encrypted_str = hash_md5.hexdigest()
        encrypted_str = generate_serial_number()
        with(open(os.path.abspath("conf/user.json"), mode="r", encoding='utf8')) as f:
            data = json.loads(f.read())
            code = data["code"]
        print('使用的激活码', code)
        print('加密后的设备码', encrypted_str)
        return code == encrypted_str
        # return True

    # def conversation_with_messages(self, user_input, TextEdit, scrollArea):
    def conversation_with_messages(self, user_input, result):
        if (not self.check_auth()):  # 检查是否激活
            # TextEdit.setMarkdown(f"申请激活，作者QQ：2778297606")
            result.emit("申请激活，作者QQ：2778297606", 0)
            # TextEdit.setFixedHeight(TextEdit.height() + TextEdit.verticalScrollBar().maximum())  # 动态更新容器高度
            # QApplication.processEvents()  # 刷新窗口
            # scrollArea.verticalScrollBar().setValue(scrollArea.verticalScrollBar().maximum())  # 置低
            return
        self.tocken_count = 0
        self.messages.append({'role': 'user', 'content': user_input})
        self.choice_key()
        status, role, full_content = self.call_with_stream(self.messages, result)
        if status:
            print("\n")
            # append result to messages.
            self.messages.append({'role': role,
                                  'content': full_content})
            self.conversation_count += 1
            print(self.tocken_count)
        else:
            print("error")
            result.emit(f"[error]可能的原因：网络连接错误/限制访问/无效的api_key:"
                        f"{self.settings['model_list'][self.model]['api_key'][self.key_index - 1]}", 0)
            # TextEdit.setMarkdown(
            #     f"[error]可能的原因：网络连接错误/限制访问/无效的api_key:"
            #     f"{self.settings['model_list'][self.model]['api_key'][self.key_index - 1]}")
            # TextEdit.setFixedHeight(TextEdit.height() + TextEdit.verticalScrollBar().maximum())  # 动态更新容器高度
            # QApplication.processEvents()  # 刷新窗口
            # scrollArea.verticalScrollBar().setValue(scrollArea.verticalScrollBar().maximum())  # 置低
        return self.tocken_count

    def clear_conversation(self):
        # self.messages = self.messages[:1]
        self.set_system(self.role)
        self.conversation_count = 0  # 对话轮数

    def choice_key(self):
        '''
        循环使用所有的key
        :return:
        '''
        keys_num = len(self.settings['model_list'][self.model]['api_key'])
        print("use api:", self.settings['model_list'][self.model]['api_key'][self.key_index])
        self.client = OpenAI(
            api_key=self.settings['model_list'][self.model]['api_key'][self.key_index],
            base_url=self.settings['model_list'][self.model]['url']
        )
        self.key_index += 1
        if (self.key_index >= keys_num):
            self.key_index = 0

    def set_system(self, name):
        self.messages.clear()
        self.role = name
        if name == "AI助手":
            SYSTEM = "你是一个乐于助人的虚拟助手，回答用户的问题，提供简洁、准确的答案，鼓励提问，建议查阅可靠来源"
            self.messages.append({'role': "system", 'content': SYSTEM})
        elif name == "中译英":
            SYSTEM = "你是一个中英翻译官，把我给你的中文翻译成英文就好。注意使用自然流畅的语言，并保持原意"
            self.messages.append({'role': "system", 'content': SYSTEM})
            self.messages.append({'role': "user", 'content': "你是什么身份"})
            self.messages.append({'role': "assistant", 'content': "我是一名中英互译的翻译官。"})
            self.messages.append({'role': "user", 'content': "我让你翻译，不是让你回答"})
            self.messages.append({'role': "assistant", 'content': "明白了，请提供需要翻译的内容。"})
        elif name == "英译中":
            SYSTEM = "帮我把英文翻译成中文"
            self.messages.append({'role': "system", 'content': SYSTEM})
        elif name == "论文润色":
            SYSTEM = "帮我润色论文内容，用更美丽、优雅、专业的词语或句子修改我的话，保持原来的意思不变"
            self.messages.append({'role': "system", 'content': SYSTEM})
        elif name == "虚拟女友":
            SYSTEM = "你将扮演我女朋友,请用女朋友的语气和我对话"
            self.messages.append({'role': "system", 'content': SYSTEM})
        elif name == "虚拟男友":
            SYSTEM = "你将扮演是我男朋友,请用男朋友的语气和我对话"
            self.messages.append({'role': "system", 'content': SYSTEM})
        elif name == "渣男":
            SYSTEM = "你将扮演一个渣男，请用渣男的语气我对话，永远不要跳脱出自己的角色，也不要承认自己是渣男"
            self.messages.append({'role': "system", 'content': SYSTEM})
        elif name == "python专家":
            SYSTEM = "你是一个python高手，精通python"
            self.messages.append({'role': "system", 'content': SYSTEM})
        elif name == "java专家":
            SYSTEM = "你是一个java高手，精通java"
            self.messages.append({'role': "system", 'content': SYSTEM})
        elif name == "c++专家":
            SYSTEM = "你是一个c++高手，精通c++"
            self.messages.append({'role': "system", 'content': SYSTEM})
        elif name == "web前端专家":
            SYSTEM = "你是一个web前端高手，精通html、css、javascript等"
            self.messages.append({'role': "system", 'content': SYSTEM})
        elif name == "web后端专家":
            SYSTEM = "你是一个web后端高手，精通Spring、MyBatis等技术框架"
            self.messages.append({'role': "system", 'content': SYSTEM})
        elif name == "linux高手":
            SYSTEM = "你是一个linux高手，擅长使用linux操作系统，能够给出linux系统下的各种操作命令"
            self.messages.append({'role': "system", 'content': SYSTEM})
        elif name == "深度学习专家":
            SYSTEM = "你是一个深度学习方面的专家，精通pytorch等深度学习框架以及各类深度学习模型"
            self.messages.append({'role': "system", 'content': SYSTEM})
        elif name == "机器学习专家":
            SYSTEM = "你是一个机器学习方面的专家，精通各类机器学习框架及各类机器学习模型和算法"
            self.messages.append({'role': "system", 'content': SYSTEM})
        else:
            SYSTEM = self.settings["role_list"][name]['prompt']
            self.messages.append({'role': "system", 'content': SYSTEM})
            if "messages" in self.settings["role_list"][name].keys():
                for msg in self.settings["role_list"][name]["messages"]:
                    self.messages.append(msg)

    def set_model(self, model_name):
        self.key_index = 0
        self.model = model_name
        self.client = OpenAI(
            api_key=self.settings['model_list'][model_name]['api_key'][0],
            base_url=self.settings['model_list'][model_name]['url']
        )

    def get_model(self):
        return self.model

    def save_conversation(self):
        with open(f"./myDialogs/{time.time()}.dlg", mode="w", encoding="utf-8") as f:
            json.dump(self.messages, f)

    def load_conversation(self, file_name):
        with open(f"./myDialogs/{file_name}.dlg", mode="r", encoding="utf-8") as f:
            self.messages = json.load(f)

    def export_conversation_to_md(self, file_path):
        with open(file_path, mode="w", encoding='utf8') as w:
            w.write(export_to_md(self.messages))
        try:
            os.startfile(file_path)
        except:
            pass

    def export_conversation_to_html(self, file_path):
        export_by_pandoc(self.messages, file_path)
        os.startfile(file_path)

    def export_conversation_to_doc(self, file_path):
        export_by_pandoc(self.messages, file_path)
        os.startfile(file_path)

    def export_conversation_to_txt(self, file_path):
        try:
            with open(file_path, mode="w", encoding='utf8') as w:
                w.write(export_to_md(self.messages))
            os.startfile(file_path)
        except:
            pass

    def export_conversation_to_pdf(self, file_path):
        pass

    def get_conversation_count(self):
        return self.conversation_count
