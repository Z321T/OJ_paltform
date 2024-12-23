from django.urls import path
from django.contrib.staticfiles.views import serve

from .views import run_code, get_result

app_name = 'Testingcode_app'

urlpatterns = [
    path('run_code/', run_code, name='run_code'),
    path('get_result/', get_result, name='get_result'),
    path('static/<path:path>', serve),
]
