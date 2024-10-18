from django.urls import path
from django.contrib.staticfiles.views import serve

from .views import home_teacher, repeat_report, repeat_report_details, repeat_code_details
from .views import profile_teacher, profile_teacher_edit, profile_teacher_password
from .views import class_teacher, create_class, delete_class, class_details, delete_student, reset_password
from .views import (repository_teacher, exercise_list_default, exercise_list,
                    create_exercise, exercise_delete, exercise_edit, exercisequestion_delete)
from .views import (exam_list_default, exam_list,
                    create_exam, exam_delete, exam_edit, examquestion_delete)
from .views import notice_teacher, create_notice, delete_notice, notification_content
from .views import (coursework_exercise, coursework_exam, coursework_adminexam, coursework_data,
                    coursework_exercise_details, coursework_exam_details, coursework_adminexam_details,
                    coursework_details_data)
from .views import standard_report, scores_details
from .views import test_check_process, get_exam_names


app_name = 'teacher_app'


urlpatterns = [
    # 教师使用界面
    path('home/', home_teacher, name='home_teacher'),
    path('home/standard_report/', standard_report, name='standard_report'),
    path('home/repeat_report/<int:programmingexercise_id>/', repeat_report, name='repeat_report'),
    path('home/repeat_report/report_details/<int:programmingexercise_id>/', repeat_report_details, name='repeat_report_details'),
    path('home/repeat_report/code_details/<int:programmingexercise_id>/', repeat_code_details, name='repeat_code_details'),
    path('home/repeat_report/scores_details/<int:programmingexercise_id>/', scores_details, name='scores_details'),
    # 有关考试实况的操作
    path('test/', test_check_process, name='test_check_process'),
    path('test/get_exam_names/', get_exam_names, name='get_exam_names'),
    # 有关的coursework操作
    path('coursework/exercise/', coursework_exercise, name='coursework_exercise'),
    path('coursework/exam/', coursework_exam, name='coursework_exam'),
    path('coursework/adminexam/', coursework_adminexam, name='coursework_adminexam'),
    path('coursework/data/', coursework_data, name='coursework_data'),
    path('coursework/exercise/details/<int:class_id>/', coursework_exercise_details, name='coursework_exercise_details'),
    path('coursework/exam/details/<int:class_id>/', coursework_exam_details, name='coursework_exam_details'),
    path('coursework/adminexam/details/<int:class_id>/', coursework_adminexam_details, name='coursework_adminexam_details'),
    path('coursework/details/data/', coursework_details_data, name='coursework_details_data'),
    # 有关通知的操作
    path('notice/', notice_teacher, name='notice_teacher'),
    path('notice/create/', create_notice, name='create_notice'),
    path('notice/delete/', delete_notice, name='delete_notice'),
    path('notice/notification_content/', notification_content, name='notification_content'),
    # 有关题库的操作：练习
    path('repository/', repository_teacher, name='repository_teacher'),
    path('repository/exercise_list/', exercise_list_default, name='exercise_list_default'),
    path('repository/exercise_list/<int:exercise_id>/', exercise_list, name='exercise_list'),
    path('repository/exercise_list/create_exercise/<int:exercise_id>/', create_exercise, name='create_exercise'),
    path('repository/delete_exercise/', exercise_delete, name='exercise_delete'),
    path('repository/edit_exercise/<int:exercise_id>/', exercise_edit, name='exercise_edit'),
    path('repository/edit_exercise/exercisequestion_delete/', exercisequestion_delete, name='exercisequestion_delete'),
    # 有关题库的操作：考试
    path('repository/exam_list/', exam_list_default, name='exam_list_default'),
    path('repository/exam_list/<int:exam_id>/', exam_list, name='exam_list'),
    path('repository/exam_list/create_exam/<int:exam_id>/', create_exam, name='create_exam'),
    path('repository/delete_exam/', exam_delete, name='exam_delete'),
    path('repository/edit_exam/<int:exam_id>/', exam_edit, name='exam_edit'),
    path('repository/edit_exam/examquestion_delete/', examquestion_delete, name='examquestion_delete'),
    # 有关班级的操作
    path('class/', class_teacher, name='class_teacher'),
    path('class/create/', create_class, name='create_class'),
    path('class/delete/', delete_class, name='delete_class'),
    path('class/class_details/<int:class_id>/', class_details, name='class_details'),
    path('class/class_details/delete_student/', delete_student, name='delete_student'),
    path('class/class_details/reset_password/', reset_password, name='reset_password'),
    # 个人中心
    path('profile/', profile_teacher, name='profile_teacher'),
    path('profile/edit/', profile_teacher_edit, name='profile_teacher_edit'),
    path('profile/password/', profile_teacher_password, name='profile_teacher_password'),

    path('static/<path:path>', serve),

]
