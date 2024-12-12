from django.urls import path
from django.contrib.staticfiles.views import serve

from .views import run_cpp_code

app_name = 'Testingcode_app'

urlpatterns = [
    path('run-cpp/', run_cpp_code, name='run-cpp'),
    path('static/<path:path>', serve),
]
