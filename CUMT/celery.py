from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# 设置Django项目的settings模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CUMT.settings')

app = Celery('celeryproject')

# 使用字符串
app.config_from_object('django.conf:settings', namespace='CELERY')

# 加载所有注册的Django app configs
app.autodiscover_tasks()
