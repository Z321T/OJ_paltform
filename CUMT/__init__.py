from __future__ import absolute_import, unicode_literals

# 确保celery app在Django项目启动时被导入。
from .celery import app as celery_app

__all__ = ('celery_app',)
