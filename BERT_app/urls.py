# BERT_app/urls.py
from django.urls import path
from django.contrib.staticfiles.views import serve

app_name = 'BERT_app'

urlpatterns = [

    path('static/<path:path>', serve),

]
