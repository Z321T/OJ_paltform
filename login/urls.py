from django.urls import path
from .views import log_in, log_out
from django.contrib.staticfiles.views import serve

app_name = 'login'

urlpatterns = [
    # 登录界面
    path('', log_in, name='log_in'),
    # 登出
    path('log_out/', log_out, name='log_out'),

    path('static/<path:path>', serve),

]
