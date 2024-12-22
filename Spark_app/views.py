# coding: utf-8
from django.http import JsonResponse

import _thread as thread
import base64
import datetime
import hashlib
import hmac
import html
import json

from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import websocket  # 使用websocket_client

# answer = ""
# sid = ''
# 全局字典，用于存储sid和answer的映射
# sid_to_answer = {}

# 以下密钥信息从控制台获取   https://console.xfyun.cn/services/bm35
appid = "1b890a23"  # 填写控制台中获取的 APPID 信息
api_secret = "ZmY4NGNmMGQ1ZWEyYjBmNmNkYjZhNDg0"  # 填写控制台中获取的 APISecret 信息
api_key = "8f3593425eb58ec2ff95c4d7716e3a36"  # 填写控制台中获取的 APIKey 信息

domain = "generalv3.5"  # v3.0版本

Spark_url = "wss://spark-api.xf-yun.com/v3.5/chat"  # v3.5环服务地址

# 初始上下文内容，当前可传system、user、assistant 等角色
text = [
    {"role": "system",
     "content": "你现在是一个代码学习助手，你会分步骤回答问题；接下来请用代码学习助手的口吻和用户对话。"},  # 设置对话背景或者模型角色
    # {"role": "user", "content": "你是谁"},  # 用户的历史问题
    # {"role": "assistant", "content": " "},  # AI的历史回答结果
    # # ....... 省略的历史对话
    # {"role": "user", "content": "你会做什么"}  # 最新的一条问题，如无需上下文，可只传最新一条问题
]


class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(Spark_url).netloc
        self.path = urlparse(Spark_url).path
        self.Spark_url = Spark_url

    # 生成url
    def create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        # 拼接鉴权参数，生成url
        url = self.Spark_url + '?' + urlencode(v)
        # print(url)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        return url


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws, one, two):
    print(" ")


# 收到websocket连接建立的处理
def on_open(ws):
    thread.start_new_thread(run, (ws,))


def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, domain=ws.domain, question=ws.question))
    ws.send(data)


class ChatConsumer:
    def __init__(self, request):
        self.request = request
        # 初始化 'answer' 键
        self.request.session['answer'] = ""

    def on_message(self, ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            print(f'请求错误: {code}, {data}')
            ws.close()
        else:
            sid = data["header"]["sid"]
            choices = data["payload"]["choices"]
            status = choices["status"]
            content = choices["text"][0]["content"]
            print(content, end="")
            self.request.session['answer'] = self.request.session.get('answer', "") + content
            if status == 2:
                ws.close()


def gen_params(appid, domain, question):
    """
    通过appid和用户的提问来生成请参数
    """
    data = {
        "header": {
            "app_id": appid,
            "uid": "1234"
        },
        "parameter": {

            "chat": {
                "domain": domain,
                "temperature": 0.8,
                "max_tokens": 2048,
                "top_k": 5,

                "auditing": "default"
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
    }
    return data


def chat(request):
    if request.method == 'POST':
        Input = request.POST.get('question')
        if Input:
            # 从session中获取text，如果不存在则创建一个新的列表
            text = request.session.get('text', [
                {"role": "system",
                 "content": "你现在是一个代码学习助手，你会分步骤回答问题；接下来请用代码学习助手的口吻和用户对话。"},
                # {"role": "assistant", "content": " "}
            ])

            # 将getText和checklen函数内联到这里，因为它们现在需要访问局部变量text
            text.append({"role": "user", "content": Input})
            while sum(len(content["content"]) for content in text) > 8000:
                del text[0]

            # 将更新后的text保存回session
            request.session['text'] = text

            wsParam = Ws_Param(appid, api_key, api_secret, Spark_url)
            websocket.enableTrace(False)
            wsUrl = wsParam.create_url()

            consumer = ChatConsumer(request)

            ws = websocket.WebSocketApp(wsUrl, on_message=consumer.on_message, on_error=on_error, on_close=on_close, on_open=on_open)
            ws.appid = appid
            ws.question = text
            ws.domain = domain
            # ws.session_id = request.session.session_key
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

            response = request.session.get('answer', "")
            response = html.escape(response)
            request.session['answer'] = ""

            text.append({"role": "assistant", "content": response})
            request.session['text'] = text

            # 使用 <pre> 标签包裹 response
            response = '<pre>' + response + '</pre>'

            return JsonResponse({'response': response})
        else:
            return JsonResponse({'error': 'No question provided'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


def clear_chat(request):
    if request.method == 'POST':
        if 'text' in request.session:
            del request.session['text']
            request.session.modified = True
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


def getText(role, content):
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = content
    text.append(jsoncon)
    return text


def getlength(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length


def checklen(text):
    while getlength(text) > 8000:
        del text[0]
    return text

