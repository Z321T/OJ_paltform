"""
Django settings for OJ_platform project.

Generated by 'django-admin startproject' using Django 5.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path
import Testingcode_app.apps
import consumer.apps
import administrator_app
import student_app.apps
import teacher_app.apps
import BERT_app.apps
import login.apps
import AIChat_app.apps
import submissions_app.apps

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-3*w5h@h=x*4=i911d!!-r+ok=2ndr&7&ejbc@my6g-mz6rz7ow'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    '*',
    'nachtohne.v7.idcfengye.com',
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 注册
    # 'django_q',
    'corsheaders',
    'student_app.apps.StudentConfig',
    'teacher_app.apps.TeacherAppConfig',
    'administrator_app.apps.AdministratorAppConfig',
    'BERT_app.apps.ScoreAppConfig',
    'login.apps.LoginConfig',
    'AIChat_app.apps.SparkAppConfig',
    "submissions_app.apps.SubmissionsAppConfig",
    "consumer.apps.ConsumerConfig",
    "Testingcode_app.apps.TestingcodeAppConfig"
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

# 会话引擎设置为数据库
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# 设置会话的过期时间为两个小时（7200秒）
SESSION_COOKIE_AGE = 7200
# 设置为 True 表示当用户关闭浏览器时会话将过期
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

ROOT_URLCONF = 'OJ_platform.urls'

CORS_ORIGIN_ALLOW_ALL = True  # 允许所有域名跨域访问


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'OJ_platform.wsgi.application'

# CSRF_COOKIE_DOMAIN = None
CSRF_TRUSTED_ORIGINS = [
    'http://nachtohne.v7.idcfengye.com',
]

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
#
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://127.0.0.1:6379/1",
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }

# 数据库配置
DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.mysql',
          'NAME': 'oj_platform',
          'USER': 'root',
          'PASSWORD': 'root',
          'HOST': '127.0.0.1',
          'PORT': 3306,
      }
  }


# # django-q的数据库配置
# Q_CLUSTER = {
#     'name': 'DjangoQ',
#     'workers': 5,
#     'recycle': 500,
#     'timeout': 60,
#     'compress': True,
#     'save_limit': 250,
#     'queue_limit': 500,
#     'cpu_affinity': 1,
#     'label': 'Django Q',
#     'django_orm': 'default',  # Use Django ORM as the broker
# }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

# 静态文件设置
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


# 没有登录时跳转的url
LOGIN_URL = '/login/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# settings.py 文件中的静态文件查找器设置
STATICFILES_FINDERS = [
    # FileSystemFinder 用于在你在 STATICFILES_DIRS 设置中指定的目录中查找静态文件。
    "django.contrib.staticfiles.finders.FileSystemFinder",

    # AppDirectoriesFinder 用于在每个安装了的应用的 "static" 子目录中查找静态文件。
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]


# 用户模型设置
AUTH_USER_MODEL = 'consumer.CustomUser'


# 密码加密设置
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# media files location
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'errors.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
