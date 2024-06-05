# coding: utf-8
from django.http import JsonResponse

from Spark_app import spark_api as SparkApi
import time

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
    {"role": "assistant", "content": " "},  # AI的历史回答结果
    # # ....... 省略的历史对话
    # {"role": "user", "content": "你会做什么"}  # 最新的一条问题，如无需上下文，可只传最新一条问题
]


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
    while (getlength(text) > 8000):
        del text[0]
    return text


# if __name__ == '__main__':
#
#     while (1):
#         Input = input("\n" + "我:")
#         question = checklen(getText("user", Input))
#         SparkApi.answer = ""
#         print("星火:", end="")
#         SparkApi.main(appid, api_key, api_secret, Spark_url, domain, question)
#         # print(SparkApi.answer)
#         getText("assistant", SparkApi.answer)


def chat(request):
    if request.method == 'POST':
        Input = request.POST.get('question')
        if Input:
            # 从session中获取text，如果不存在则创建一个新的列表
            text = request.session.get('text', [
                {"role": "system",
                 "content": "你现在是一个代码学习助手，你会分步骤回答问题；接下来请用代码学习助手的口吻和用户对话。"},
                {"role": "assistant", "content": " "}
            ])

            # 将getText和checklen函数内联到这里，因为它们现在需要访问局部变量text
            text.append({"role": "user", "content": Input})
            while sum(len(content["content"]) for content in text) > 8000:
                del text[0]

            # 将更新后的text保存回session
            request.session['text'] = text

            SparkApi.main(appid, api_key, api_secret, Spark_url, domain, text)
            response = SparkApi.answer
            text.append({"role": "assistant", "content": response})
            request.session['text'] = text

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

    #         question = checklen(getText("user", Input))
    #         SparkApi.main(appid, api_key, api_secret, Spark_url, domain, question)
    #         response = SparkApi.answer
    #         getText("assistant", response)
    #         return JsonResponse({'response': response})
    #     else:
    #         return JsonResponse({'error': 'No question provided'}, status=400)
    # else:
    #     return JsonResponse({'error': 'Invalid request'}, status=400)