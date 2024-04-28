import json

from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render, redirect

from administrator_app.models import Administrator
from student_app.models import Student
from teacher_app.models import Teacher


# Create your views here.
def log_in(request):
    if request.method == 'POST':
        # 获取表单提交的用户名和密码
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        user = None
        user_type = None

        if Student.objects.filter(userid=username).exists():
            user = Student.objects.get(userid=username)
            if check_password(password, user.password):
                user_type = 'student'
            else:
                user = None
        elif Teacher.objects.filter(userid=username).exists():
            user = Teacher.objects.get(userid=username)
            if check_password(password, user.password):
                user_type = 'teacher'
            else:
                user = None
        elif Administrator.objects.filter(userid=username).exists():
            user = Administrator.objects.get(userid=username)
            if check_password(password, user.password):
                user_type = 'administrator'
            else:
                user = None
        else:
            error_message = 'Userid is incorrect'
            return JsonResponse({'status': 'error', 'message': error_message})

        if user is not None:
            # 用户验证成功，登录用户
            login(request, user)
            request.session['user_id'] = user.userid
            return JsonResponse({'status': 'success', 'message': user_type})
        else:
            # 用户验证失败，显示不同的错误消息
            error_message = 'Password is incorrect'
            return JsonResponse({'status': 'error', 'message': error_message})

    return render(request, "log_in.html")


def log_out(request):
    # 使用Django的logout函数清除用户session
    logout(request)
    # 返回注销成功的消息
    return redirect('login:log_in')


# 检测用户是否登录
def check_login(user_id):
    if user_id is None:
        return True
    for model in (Administrator, Teacher, Student):
        try:
            model.objects.get(userid=user_id)
            return False
        except ObjectDoesNotExist:
            continue
    return True
