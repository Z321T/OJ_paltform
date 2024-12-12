# student_app/urls.py
from django.urls import path
from django.contrib.staticfiles.views import serve

from .views import home_student, practice_student, exam_student, profile_student, report_student
from .views import teacherexam_list, practice_list, notification_content, adminexam_list
from .views import analyse_exercise, analyse_exam, analyse_data
from .views import coding_exercise, coding_exam, coding_adminexam
from .views import profile_student_edit, profile_student_password
# 开发环境配置
from django.conf import settings
from django.conf.urls.static import static


app_name = 'student_app'


urlpatterns = [
    # 学生主页
    path('home/', home_student, name='home_student'),
    path('home/report_student/<int:programmingexercise_id>/', report_student, name='report_student'),
    # 练习相关
    path('practice/', practice_student, name='practice_student'),
    path('practice/practice_list/<int:exercise_id>/', practice_list, name='practice_list'),
    path('coding_exercise/<int:exercisequestion_id>/', coding_exercise, name='coding_exercise'),
    # 考试相关
    path('exam/', exam_student, name='exam_student'),
    path('exam/exam_list/<int:exam_id>/', teacherexam_list, name='teacherexam_list'),
    path('exam/adminexam_list/<int:exam_id>/', adminexam_list, name='adminexam_list'),
    path('coding_exam/<int:examquestion_id>/', coding_exam, name='coding_exam'),
    path('coding_adminexam/<int:examquestion_id>/', coding_adminexam, name='coding_adminexam'),
    # 学情分析相关
    path('analyse_exercise/', analyse_exercise, name='analyse_exercise'),
    path('analyse_exam/', analyse_exam, name='analyse_exam'),
    path('analyse_data/', analyse_data, name='analyse_data'),
    # 学生个人中心
    path('profile/', profile_student, name='profile_student'),
    path('profile/edit/', profile_student_edit, name='profile_student_edit'),
    path('profile/password/', profile_student_password, name='profile_student_password'),
    # 通知相关
    path('notification_content/', notification_content, name='notification_content'),

    path('static/<path:path>', serve),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


