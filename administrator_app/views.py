import os
import tempfile
import docx
import logging
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from BERT_app.views import analyze_programming_report, analyze_programming_code
from administrator_app.models import (Administrator, AdminNotification, ProgrammingExercise,
                                      AdminExam, AdminExamQuestion, AdminExamQuestionTestCase)
from teacher_app.models import Teacher, Class
from student_app.models import Student, Score
from BERT_app.models import ReportStandardScore, ProgrammingCodeFeature, ProgrammingReportFeature
from login.views import login_required
from submissions_app.models import GradeExamSubmission


# 课程负责人主页-程序设计
@login_required
def home_administrator(request):
    try:
        # 尝试从会话中获取用户ID
        user_id = request.session.get('user_id')

        # 尝试获取编程练习信息，并按日期倒序排列
        programings = ProgrammingExercise.objects.all().order_by('-date_posted')

        # 构建上下文
        context = {
            'active_page': 'home',
            'user_id': user_id,
            'coursework': programings,
        }

        # 正常渲染页面
        return render(request, 'home_administrator.html', context)

    # 捕获会话获取错误
    except KeyError:
        logging.error("Failed to get user_id from session.")
        return render(request, 'error.html', {'message': "会话中未找到用户ID"}, status=400)

    # 捕获数据库相关错误
    except DatabaseError as db_err:
        logging.error(f"Database operation failed: {str(db_err)}")
        return render(request, 'error.html', {'message': "无法连接到数据库，请稍后重试"}, status=500)

    # 捕获其他未预见的错误
    except Exception as e:
        logging.error(f"An unknown error occurred: {str(e)}")
        return render(request, 'error.html', {'message': f"发生未知错误: {e}"}, status=500)


# 课程负责人主页-年级考试
@login_required
def home_administrator_exam(request):
    try:
        # 尝试从会话中获取用户ID
        user_id = request.session.get('user_id')

        # 尝试删除标题为"默认标题"的记录
        AdminExam.objects.filter(title="默认标题").delete()

        # 获取所有考试信息，并按开始时间倒序排列
        exams = AdminExam.objects.all().order_by('-starttime')

        # 构建上下文
        context = {
            'active_page': 'home',
            'user_id': user_id,
            'coursework': exams,
        }

        # 正常渲染页面
        return render(request, 'home_administrator_exam.html', context)

        # 捕获会话获取错误
    except KeyError:
        logging.error("Failed to get user_id from session.")
        return render(request, 'error.html', {'message': "会话中未找到用户ID"}, status=400)

        # 捕获数据库相关错误
    except DatabaseError as db_err:
        logging.error(f"Database operation failed: {str(db_err)}")
        return render(request, 'error.html', {'message': "数据库操作失败，请稍后重试"}, status=500)

        # 捕获其他未预见的错误
    except Exception as e:
        logging.error(f"An unknown error occurred: {str(e)}")
        return render(request, 'error.html', {'message': f"发生未知错误: {e}"}, status=500)


# 课程负责人主页-程序设计题详情
@login_required
def programmingexercise_details_data(request):
    try:
        if request.method == 'POST':
            question_id = request.POST.get('id')

            # 尝试获取指定的编程练习题
            try:
                question = ProgrammingExercise.objects.get(id=question_id)
                total_students = Student.objects.count()
                total_submissions = ReportStandardScore.objects.filter(programming_question=question).count()
                ratio = total_submissions / total_students if total_students else 0
                ratio_data = [{
                    'completion_rate': ratio,
                }]

                context = {
                    'ratio_data': ratio_data,
                }
                return JsonResponse({'data': context}, status=200)

            except ProgrammingExercise.DoesNotExist:
                logging.error(f"ProgrammingExercise with id {question_id} does not exist.")
                return JsonResponse({'status': 'error', 'message': '未找到对应的练习题'}, status=404)
        else:
            logging.warning("Invalid request method used for programmingexercise_details_data.")
            return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)

    # 捕获数据库相关错误
    except DatabaseError as db_err:
        logging.error(f"Database operation failed: {str(db_err)}")
        return JsonResponse({'status': 'error', 'message': '数据库操作失败，请稍后重试'}, status=500)

    # 捕获其他未预见的错误
    except Exception as e:
        logging.error(f"An unknown error occurred: {str(e)}")
        return JsonResponse({'status': 'error', 'message': f'发生未知错误: {e}'}, status=500)


# 课程负责人主页-年级考试题详情
@login_required
def exam_details_data(request):
    try:
        if request.method == 'POST':
            exam_id = request.POST.get('id')

            # 尝试获取指定的考试
            try:
                exam = AdminExam.objects.get(id=exam_id)
                questions = exam.questions.all()
                question_avg_scores = []

                for question in questions:
                    # 获取当前题目所有分数对象
                    scores = Score.objects.filter(adminexam=exam, adminexam_question=question)
                    total_score = sum(score.score for score in scores)
                    total_students = Student.objects.count()
                    # 计算平均分，若学生总数为0，则平均分为0
                    avg_score = (total_score / total_students) if total_students else 0

                    question_avg_scores.append({
                        'question_title': question.title,
                        'average_score': avg_score
                    })

                return JsonResponse({'data': question_avg_scores}, status=200)

            except AdminExam.DoesNotExist:
                logging.error(f"AdminExam with id {exam_id} does not exist.")
                return JsonResponse({'status': 'error', 'message': '未找到对应的考试'}, status=404)
        else:
            logging.warning("Invalid request method used for exam_details_data.")
            return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)

    # 捕获数据库相关错误
    except DatabaseError as db_err:
        logging.error(f"Database operation failed: {str(db_err)}")
        return JsonResponse({'status': 'error', 'message': '数据库操作失败，请稍后重试'}, status=500)

    # 捕获其他未预见的错误
    except Exception as e:
        logging.error(f"An unknown error occurred: {str(e)}")
        return JsonResponse({'status': 'error', 'message': f'发生未知错误: {e}'}, status=500)


# 年级考试实况
@login_required
def admintest_check_process(request):
    user_id = request.session.get('user_id')

    # 获取 exam_type 和 exam_id 参数
    exam_type = request.GET.get('exam_type')
    exam_id = request.GET.get('exam_id')
    selected_exam = None
    submissions = []

    # 检查 exam_type 和 exam_id 的有效性
    if not exam_type or not exam_id:
        return JsonResponse({'status': 'error', 'message': '参数缺失：考试类型 或 考试内容 无效。'}, status=400)

    # 检查 exam_id 是否为有效整数
    try:
        exam_id = int(exam_id)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': '请求中含有无效的参数'}, status=400)

    try:
        # 根据 exam_type 获取考试
        if exam_type == 'adminexam':
            selected_exam = AdminExam.objects.filter(id=exam_id).first()
            if selected_exam:
                submissions = GradeExamSubmission.objects.filter(exam=selected_exam).order_by('-submission_time')
            else:
                return JsonResponse({'status': 'error', 'message': '未找到相应的考试记录。'}, status=404)
        else:
            return JsonResponse({'status': 'error', 'message': '无效的 考试类型 参数。'}, status=400)
    except AdminExam.DoesNotExist:
        logging.error(f"AdminExam with id {exam_id} does not exist.")
        return JsonResponse({'status': 'error', 'message': '未找到相应的考试记录，可能已被删除。'}, status=404)
    except GradeExamSubmission.DoesNotExist:
        logging.error(f"No GradeExamSubmission found for exam id {exam_id}.")
        return JsonResponse({'status': 'error', 'message': '无法加载提交记录，可能数据库中不存在相关数据。'}, status=404)
    except DatabaseError as db_err:
        logging.error(f"Database operation failed: {str(db_err)}")
        return JsonResponse({'status': 'error', 'message': '数据库操作失败，请稍后重试。'}, status=500)
    except Exception as e:
        # 捕获其他异常，防止应用崩溃
        logging.error(f"An unknown error occurred: {str(e)}")
        return JsonResponse({'status': 'error', 'message': f'发生未知错误: {e}'}, status=500)

    context = {
        'active_page': 'testcheck',
        'user_id': user_id,
        'selected_exam': selected_exam,
        'submissions': submissions,
        'exam_type': exam_type,
        'exam_id': exam_id,
    }
    return render(request, 'admintest_check_process.html', context)


# 年级考试实况-获取考试项目
@login_required
def get_adminexam_names(request):
    exam_type = request.GET.get('exam_type')
    user_id = request.session.get('user_id')

    try:
        admin = Administrator.objects.get(userid=user_id)

        if exam_type == 'adminexam':
            exams = AdminExam.objects.filter(teacher=admin)
        else:
            exams = []

        exam_names = [{'id': exam.id, 'name': exam.title} for exam in exams]
        return JsonResponse({'exam_names': exam_names}, status=200)
    except Administrator.DoesNotExist:
        logging.error(f"Administrator with user_id {user_id} does not exist.")
        return JsonResponse({'status': 'error', 'message': '未找到管理员信息，请确认用户是否为管理员。'}, status=404)
    except DatabaseError as db_err:
        logging.error(f"Database operation failed: {str(db_err)}")
        return JsonResponse({'status': 'error', 'message': '数据库操作失败，请稍后重试。'}, status=500)
    except Exception as e:
        logging.error(f"An unknown error occurred: {str(e)}")
        return JsonResponse({'status': 'error', 'message': f'发生未知错误: {e}'}, status=500)


# GUI程序设计题库
@login_required
def repository_administrator(request):
    user_id = request.session.get('user_id')

    programming_exercises = ProgrammingExercise.objects.all().order_by('-date_posted')

    context = {
        'active_page': 'guirepository',
        'user_id': user_id,
        'programming_exercises': programming_exercises,
    }
    return render(request, 'repository_administrator.html', context)


# 程序设计题库：添加程序设计题
@login_required
def programmingexercise_create(request):
    user_id = request.session.get('user_id')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('content')
        deadline = request.POST.get('deadline')
        posted_by = request.session.get('user_id')

        if title and description and deadline and posted_by:
            ProgrammingExercise.objects.create(
                title=title,
                description=description,
                deadline=deadline,
                posted_by=Administrator.objects.get(userid=posted_by)
            )
            return redirect('administrator_app:repository_administrator')

    conetxt = {
        'active_page': 'guirepository',
        'user_id': user_id,
    }
    return render(request, 'programmingexercise_create.html', conetxt)


# 程序设计题库：删除程序设计题
@login_required
def programmingexercise_delete(request):

    if request.method == 'POST':
        exercise_id = request.POST.get('exercise_id')
        if exercise_id:
            exercise_to_delete = ProgrammingExercise.objects.filter(id=exercise_id)
            exercise_to_delete.delete()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': '练习未找到'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


# 题库查重管理
@login_required
def problems_administrator(request):
    user_id = request.session.get('user_id')

    programming_exercises = ProgrammingExercise.objects.all().order_by('-date_posted')

    context = {
        'active_page': 'problemsmanage',
        'user_id': user_id,
        'programming_exercises': programming_exercises,
    }
    return render(request, 'problems_administrator.html', context)


# 题库查重管理-导入数据
@login_required
def report_administrator(request):
    user_id = request.session.get('user_id')

    programmingexercise_id = request.GET.get('exerciseId')

    if request.method == 'POST':
        student = None
        word_file = request.FILES['wordFile']

        if word_file:
            # 读取文件内容并使用BytesIO创建一个类似文件的对象
            word_file_bytes = BytesIO(word_file.read())
            # 使用BytesIO对象创建docx文档对象
            document = docx.Document(word_file_bytes)
            full_text = []
            for paragraph in document.paragraphs:
                full_text.append(paragraph.text)
            # 获得纯文本代码，去除了图片
            report = '\n'.join(full_text)
            # 分析报告特征
            analyze_programming_report(student, report, programmingexercise_id)

        # 读取TXT文件内容
        code_file = request.FILES.get('txtFile')
        if code_file:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            temp_file.write(code_file.read())
            temp_file.close()
            # 分析代码特征
            code = open(temp_file.name, encoding='utf-8').read()
            analyze_programming_code(student, code, programmingexercise_id)
            os.unlink(temp_file.name)
        return JsonResponse({'status': 'success', 'message': '提交成功'}, status=200)

    context = {
        'active_page': 'problemsmanage',
        'user_id': user_id,
    }
    return render(request, 'report_administrator.html', context)


# 题库查重管理-删除数据
@login_required
def reportdata_delete(request):

    programmingexercise_id = request.POST.get('exerciseId')
    if programmingexercise_id:
        # 查询对应题目所有student为null的ProgrammingCodeFeature实例
        programmingexercise = ProgrammingExercise.objects.get(id=programmingexercise_id)

        codefeatures_to_delete = ProgrammingCodeFeature.objects.filter(
            programming_question=programmingexercise,
            student__isnull=True
        )
        # 执行删除操作
        codefeatures_to_delete.delete()

        reportfeatures_to_delete = ProgrammingReportFeature.objects.filter(
            programming_question=programmingexercise,
            student__isnull=True
        )
        reportfeatures_to_delete.delete()

        return JsonResponse({'status': 'success', 'message': '数据删除成功'}, status=200)
    else:
        return JsonResponse({'status': 'error', 'message': '未找到对应的练习题'}, status=404)


# 年级考试
@login_required
def exam_administrator(request):
    user_id = request.session.get('user_id')

    AdminExam.objects.filter(title="默认标题").delete()
    exams = AdminExam.objects.all().order_by('-starttime')

    context = {
        'active_page': 'adminexam',
        'user_id': user_id,
        'exams': exams,
    }
    return render(request, 'exam_administrator.html', context)


# 考试-考试列表
@login_required
def admin_examlist_default(request):
    user_id = request.session.get('user_id')

    admin = Administrator.objects.get(userid=user_id)
    exam = AdminExam.objects.create(
        title="默认标题",
        content="默认内容",
        starttime=datetime.now(),
        deadline=datetime.now() + timedelta(days=7),
        teacher=admin
    )

    context = {
        'active_page': 'adminexam',
        'user_id': user_id,
        'exam': exam,
    }

    return render(request, 'admin_examlist.html', context)


@login_required
def admin_examlist(request, exam_id):
    user_id = request.session.get('user_id')

    exam = get_object_or_404(AdminExam, id=exam_id)

    if request.method == 'POST':
        exam.title = request.POST.get('title')
        exam.content = request.POST.get('content')
        exam.starttime = request.POST.get('starttime')
        exam.deadline = request.POST.get('deadline')

        recipient_class = Class.objects.all()
        if recipient_class:
            exam.save()
            exam.classes.set(recipient_class)
            return redirect('administrator_app:exam_administrator')

    context = {
        'active_page': 'adminexam',
        'user_id': user_id,
        'exam': exam,
    }
    return render(request, 'admin_examlist.html', context)


# 考试-考试列表-创建考试题
@login_required
def create_adminexam(request, exam_id):
    user_id = request.session.get('user_id')

    exam = get_object_or_404(AdminExam, id=exam_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        memory_limit = request.POST.get('memory_limit')
        time_limit = request.POST.get('time_limit')

        question = AdminExamQuestion(exam=exam, title=title, content=content,
                                     memory_limit=memory_limit, time_limit=time_limit)
        question.save()

        # 遍历提交的测试用例
        for key in request.POST.keys():
            if key.startswith('input'):
                testcase_num = key[5:]  # 获取测试用例的编号
                input_data = request.POST.get('input' + testcase_num)
                output_data = request.POST.get('output' + testcase_num)

                # 创建一个新的AdminExamQuestionTestCase实例
                testcase = AdminExamQuestionTestCase(question=question, input=input_data, expected_output=output_data)
                testcase.save()

        return redirect('administrator_app:admin_examlist', exam_id=exam.id)

    context = {
        'active_page': 'adminexam',
        'user_id': user_id,
        'exam': exam,
    }
    return render(request, 'create_adminexam.html', context)


# 考试-考试列表-修改考试题
@login_required
def adminexam_edit(request, exam_id):
    user_id = request.session.get('user_id')

    if request.method == 'GET':
        exam = AdminExam.objects.get(id=exam_id)
        context = {
            'active_page': 'adminexam',
            'user_id': user_id,
            'exam': exam,
        }
        return render(request, 'adminexam_edit.html', context)


# 考试-考试列表-删除考试
@login_required
def adminexam_delete(request):

    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        if exam_id:
            exam_to_delete = AdminExam.objects.filter(id=exam_id).first()
            if exam_to_delete:
                exam_to_delete.questions.all().delete()
                exam_to_delete.classes.clear()
                exam_to_delete.delete()
                return JsonResponse({'status': 'success'}, status=200)
        return JsonResponse({'status': 'error', 'message': '考试未找到'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


# 考试-考试列表-删除考试题
@login_required
def adminexamquestion_delete(request):

    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        if question_id:
            question_to_delete = AdminExamQuestion.objects.filter(id=question_id).first()
            if question_to_delete:
                question_to_delete.delete()
                return JsonResponse({'status': 'success'}, status=200)
        return JsonResponse({'status': 'error', 'message': '考试题未找到'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


# 通知界面
@login_required
def notice_administrator(request):
    user_id = request.session.get('user_id')

    adminnotifications = AdminNotification.objects.all().order_by('-date_posted').distinct()

    context = {
        'active_page': 'notice',
        'user_id': user_id,
        'adminnotifications': adminnotifications,
    }
    return render(request, 'notice_administrator.html', context)


# 通知界面：发布通知
@login_required
def create_notice(request):
    user_id = request.session.get('user_id')

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('message')
        if title and content:
            adminnotification = AdminNotification.objects.create(
                title=title,
                content=content,
            )
            adminnotification.save()
            return redirect('administrator_app:notice_administrator')

    context = {
        'active_page': 'notice',
        'user_id': user_id,
    }
    return render(request, 'create_notice_admin.html', context)


# 通知界面：删除通知
@login_required
def delete_notice(request):

    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        try:
            notification = AdminNotification.objects.filter(id=notification_id).first()
            notification.delete()
            return JsonResponse({'status': 'success'}, status=200)
        except AdminNotification.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '通知未找到'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


# 通知界面：通知内容
@login_required
def notification_content(request):

    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        notification = AdminNotification.objects.get(id=notification_id)
        return JsonResponse({'title': notification.title, 'content': notification.content}, status=200)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


# 教师管理
@login_required
def information_administrator(request):
    user_id = request.session.get('user_id')

    teachers = Teacher.objects.all()

    context = {
        'active_page': 'teachermanage',
        'user_id': user_id,
        'teachers': teachers,
    }
    return render(request, 'information_administrator.html', context)


# 教师管理：添加教师
@login_required
def add_teacher(request):
    user_id = request.session.get('user_id')

    if request.method == 'POST':
        initial_password = request.POST.get('initialPassword')
        file = request.FILES.get('excelFile')

        if initial_password and file:
            data = pd.read_excel(file)
            for index, row in data.iterrows():
                hashed_password = make_password(initial_password)
                Teacher.objects.create(
                    name=row['姓名'],
                    userid=row['教工号'],
                    password=hashed_password,
                )
            return redirect('administrator_app:information_administrator')

    context = {
        'active_page': 'teachermanage',
        'user_id': user_id,
    }
    return render(request, 'add_teacher.html', context)


# 教师管理：删除教师
@login_required
def delete_teacher(request):

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            teacher.delete()
            return JsonResponse({'status': 'success', 'message': '教师删除成功'}, status=200)
        except Teacher.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '教师未找到'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


# 教师管理：重置密码
@login_required
def reset_password(request):

    if request.method == 'POST':
        teacher = Teacher.objects.get(id=request.POST.get('teacher_id'))
        try:
            initial_password = 'cumt1909'  # 设置为默认密码
            hashed_password = make_password(initial_password)
            teacher.password = hashed_password
            teacher.save()
            return JsonResponse({'status': 'success', 'message': '初始化成功，密码改为cumt1909'}, status=200)
        except Teacher.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '初始化密码失败'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


# 管理员个人中心
@login_required
def profile_administrator(request):
    user_id = request.session.get('user_id')

    administrator = Administrator.objects.get(userid=request.session.get('user_id'))

    context = {
        'active_page': 'profile',
        'user_id': user_id,
        'administrator': administrator,
    }
    return render(request, 'profile_administrator.html', context)


# 管理员个人中心：修改个人信息
@login_required
def profile_administrator_edit(request):
    user_id = request.session.get('user_id')

    administrator = Administrator.objects.get(userid=request.session.get('user_id'))

    context = {
        'active_page': 'profile',
        'user_id': user_id,
        'administrator': administrator,
    }

    if request.method == 'POST':
        phone_num = request.POST.get('phone_num')
        email = request.POST.get('email')
        administrator.phone_num = phone_num
        administrator.email = email
        administrator.save()
        return redirect('administrator_app:profile_administrator')

    return render(request, 'profile_administrator_edit.html', context)


# 管理员个人中心-修改密码
@login_required
def profile_adminadministrator_password(request):
    user_id = request.session.get('user_id')

    administrator = Administrator.objects.get(userid=user_id)

    context = {
        'active_page': 'profile',
        'user_id': user_id,
    }

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if check_password(old_password, administrator.password):
            if new_password == confirm_password:
                administrator.password = make_password(new_password)
                administrator.save()
                return JsonResponse({'status': 'success', 'message': '密码修改成功'}, status=200)
            else:
                return JsonResponse({'status': 'error', 'message': '两次输入的密码不一致'}, status=400)
        else:
            return JsonResponse({'status': 'error', 'message': '旧密码错误'}, status=400)

    return render(request, 'password_admin_edit.html', context)



