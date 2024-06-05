"""
URL configuration for CUMT project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include
from django.contrib import admin

urlpatterns = [

    # 统一登录界面
    path('login/', include('login.urls')),

    # 学生使用界面
    path('student/', include('student_app.urls')),

    # 教师使用界面
    path('teacher/', include('teacher_app.urls')),

    # 超级管理员使用界面
    path('administrator/', include('administrator_app.urls')),

    # 代码查重
    path('codebert/', include('CodeBERT_app.urls')),

    # Django后端管理界面
    path('admin/', admin.site.urls),

    # 讯飞星火智能对话
    path('Spark/', include('Spark_app.urls')),
]

