import json

from functools import wraps
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.shortcuts import render, redirect

from administrator_app.models import Administrator
from student_app.models import Student
from teacher_app.models import Teacher


# Create your views here.
def log_in(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        # 定义子类模型列表
        models_to_check = [Student, Teacher, Administrator]
        user = None
        user_model = None

        # 分步查询每个子类模型
        for model in models_to_check:
            user = model.objects.filter(userid=username).first()
            if user:
                user_model = model.__name__  # 记录模型名称
                break

        if not user:
            return JsonResponse({'status': 'error', 'message': 'Userid is incorrect'})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            user_type = user_model.lower() # 将模型名称转换为小写
            return JsonResponse({'status': 'success', 'message': user_type})
        else:
            return JsonResponse({'status': 'error', 'message': 'Password is incorrect'})

    return render(request, "log_in.html")


def log_out(request):
    logout(request)
    return redirect('login:log_in')


def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')
        return view_func(request, *args, **kwargs)
    return wrapper

