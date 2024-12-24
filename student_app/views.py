import os
import docx
import tempfile
from io import BytesIO

from django.utils import timezone
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password

from administrator_app.models import ProgrammingExercise, AdminExam, AdminExamQuestion
from student_app.models import Student
from teacher_app.models import Notification, Exercise, Exam, ExerciseQuestion, ExamQuestion, ReportScore
from BERT_app.views import (analyze_programming_report,
                            score_report, analyze_programming_code)
from login.views import login_required
from Testingcode_app.models import (Score)


# 学生主页
@login_required
def home_student(request):
    student = Student.objects.get(pk=request.user.pk)
    user_id = student.userid
    # 获取学生所在班级的通知
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    # 获取GUI编程题目
    teacher = student.class_assigned.teacher
    programing_exercises = ProgrammingExercise.objects.filter(posted_by=teacher.course_coordinator).order_by('-date_posted')
    # 前端模版渲染内容
    context = {
        'active_page': 'home',
        'user_id': user_id,
        'notifications': notifications,
        'programing_exercises': programing_exercises,
    }
    return render(request, 'home_student.html', context)

# 学生主页：提交报告
@login_required
def report_student(request, programmingexercise_id):
    student = Student.objects.get(pk=request.user.pk)
    user_id = student.userid
    # 获取课程负责人发布的GUI编程题目
    programming_exercise = get_object_or_404(ProgrammingExercise, id=programmingexercise_id)
    # GET请求时发送渲染内容，并获取学生所在班级的通知
    if request.method == 'GET':
        notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
        # 前端模版渲染内容
        context = {
            'active_page': 'home',
            'user_id': user_id,
            'notifications': notifications,
            'programming_exercise': programming_exercise,
        }
        return render(request, 'report_student.html', context)
    # 检查截止时间
    if timezone.now() > programming_exercise.deadline:
        return JsonResponse({'status': 'error', 'message': '截止时间已到，不能提交报告'}, status=400)
    # POST请求时处理提交的报告
    if request.method == 'POST':
        reportstandards = ReportScore.objects.filter(teacher=student.class_assigned.teacher)
        if reportstandards:
            word_file = request.FILES.get('wordFile')
            if word_file:
                try:
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
                    # 报告规范性评分
                    score_report(student, document, programmingexercise_id)
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': f'处理Word文件时出错: {str(e)}'}, status=400)
            # 读取TXT文件内容
            code_file = request.FILES.get('txtFile')
            if code_file:
                try:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
                    temp_file.write(code_file.read())
                    temp_file.close()
                    # 分析代码特征
                    code = open(temp_file.name, encoding='utf-8').read()
                    analyze_programming_code(student, code, programmingexercise_id)
                    # 删除临时文件
                    os.unlink(temp_file.name)
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': f'处理TXT文件时出错: {str(e)}'}, status=400)
            return JsonResponse({'status': 'success', 'message': '提交成功'}, status=200)
        else:
            return JsonResponse({'status': 'error', 'message': '教师未设置报告规范性评分标准'}, status=400)

# 我的练习
@login_required
def practice_student(request):
    student = Student.objects.get(pk=request.user.pk)
    user_id = student.userid
    # 获取学生所在班级的通知、班级的练习题目
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    exercises = Exercise.objects.filter(classes=student.class_assigned).order_by('-published_at')
    # 前端模版渲染内容
    context = {
        'active_page': 'practice',
        'user_id': user_id,
        'exercises': exercises,
        'notifications': notifications,
    }
    return render(request, 'practice_student.html', context)

# 我的练习：练习详情
@login_required
def practice_list(request, exercise_id):
    student = Student.objects.get(pk=request.user.pk)
    user_id = student.userid
    # 获取学生所在班级的通知
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    if request.method == 'GET':
        exercise = Exercise.objects.get(id=exercise_id)
        # 前端模版渲染内容
        context = {
            'active_page': 'practice',
            'user_id': user_id,
            'exercise': exercise,
            'notifications': notifications,
        }
        return render(request, 'practice_list.html', context)

# 我的考试
@login_required
def exam_student(request):
    student = Student.objects.get(pk=request.user.pk)
    user_id = student.userid
    # 获取学生所在班级的通知、教师发布的班级考试th_exams、课程负责人发布的年级考试admin_exams
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    th_exams = Exam.objects.filter(classes=student.class_assigned).order_by('-starttime')
    admin_exams = AdminExam.objects.filter(classes=student.class_assigned).order_by('-starttime')
    # 前端模版渲染内容
    context = {
        'active_page': 'exam',
        'user_id': user_id,
        'th_exams': th_exams,
        'admin_exams': admin_exams,
        'notifications': notifications,
    }
    return render(request, 'exam_student.html', context)

# 我的考试：教师考试详情
@login_required
def teacherexam_list(request, exam_id):
    student = Student.objects.get(pk=request.user.pk)
    user_id = student.userid
    # 获取学生所在班级的通知
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    if request.method == 'GET':
        exam = Exam.objects.get(id=exam_id)
        # 前端模版渲染内容
        context = {
            'active_page': 'exam',
            'user_id': user_id,
            'exam': exam,
            'notifications': notifications,
        }
        return render(request, 'teacherexam_list.html', context)

# 我的考试：管理员考试详情
@login_required
def adminexam_list(request, exam_id):
    student = Student.objects.get(pk=request.user.pk)
    user_id = student.userid
    # 获取学生所在班级的通知
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    if request.method == 'GET':
        exam = AdminExam.objects.get(id=exam_id)
        # 前端模版渲染内容
        context = {
            'active_page': 'exam',
            'user_id': user_id,
            'exam': exam,
            'notifications': notifications,
        }
        return render(request, 'adminexam_list.html', context)

# 学情分析-班级练习
@login_required
def analyse_exercise(request):
    student = Student.objects.get(pk=request.user.pk)
    user_id = student.userid
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    exercises = Exercise.objects.filter(classes=student.class_assigned).order_by('-published_at')
    # 前端模版渲染内容
    context = {
        'active_page': 'analyse',
        'user_id': user_id,
        'notifications': notifications,
        'coursework': exercises,
    }
    return render(request, 'analyse_exercise.html', context)

# 学情分析-班级考试
@login_required
def analyse_exam(request):
    student = Student.objects.get(pk=request.user.pk)
    user_id = student.userid
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    exams = Exam.objects.filter(classes=student.class_assigned).order_by('-starttime')
    # 前端模版渲染内容
    context = {
        'active_page': 'analyse',
        'user_id': user_id,
        'notifications': notifications,
        'coursework': exams,
    }
    return render(request, 'analyse_exam.html', context)

# 学情分析-获取数据
@login_required
def analyse_data(request):
    student = Student.objects.get(pk=request.user.pk)
    class_assigned = student.class_assigned
    if request.method == 'POST':
        data_type = request.POST.get('type')
        item_id = request.POST.get('id')
        # 获取练习的平均得分和题目得分
        if data_type == 'exercise':
            # 计算每个练习的平均得分
            exercises = Exercise.objects.filter(classes=class_assigned)
            exercise_avg_scores = []
            for ex in exercises:
                question_count = ex.questions.count()  # 使用 related_name 获取相关的练习题数量
                ex_questions = ExerciseQuestion.objects.filter(exercise=ex)
                # 计算这次练习的所有题目的总得分
                total_score = Score.objects.filter(
                    student=student,
                    exercise=ex,
                    exercise_question__in=ex_questions
                ).aggregate(total_score=Sum('score'))['total_score']

                if total_score is None:
                    total_score = 0
                avg_score = total_score / question_count  # 计算平均得分 (总得分 / 题目数量)

                exercise_avg_scores.append({
                    'exercise_title': ex.title,
                    'avg_score': avg_score
                })

            # 获取每个练习题的得分
            exercise = get_object_or_404(Exercise, id=item_id)
            questions = ExerciseQuestion.objects.filter(exercise=exercise)
            question_scores = []
            for question in questions:
                try:
                    score_obj = Score.objects.get(student=student, exercise=exercise, exercise_question=question)
                    score = float(score_obj.score)
                except Score.DoesNotExist:  # 如果没有找到得分，则为该题目设置得分为0
                    score = 0.0

                question_scores.append({
                    'question_title': question.title,
                    'scores': score
                })

            context = {
                'avg_scores': exercise_avg_scores,
                'question_scores': question_scores,
            }
            return JsonResponse({'data': context}, status=200)

        elif data_type == 'exam':
            # 计算每个考试的平均得分
            exam = Exam.objects.filter(classes=class_assigned)
            exam_avg_scores = []
            for ex in exam:
                question_count = ex.questions.count()
                ex_questions = ExamQuestion.objects.filter(exam=ex)
                total_score = Score.objects.filter(
                    student=student,
                    exam=ex,
                    exam_question__in=ex_questions
                ).aggregate(total_score=Sum('score'))['total_score']

                if total_score is None:
                    total_score = 0
                avg_score = total_score / question_count

                exam_avg_scores.append({
                    'exam_title': ex.title,
                    'avg_score': avg_score
                })

            # 获取每个考试题的得分
            exam = get_object_or_404(Exam, id=item_id)
            questions = ExamQuestion.objects.filter(exam=exam)
            question_scores = []
            for question in questions:
                try:
                    score_obj = Score.objects.get(student=student, exam=exam, exam_question=question)
                    score = float(score_obj.score)
                except Score.DoesNotExist:
                    score = 0.0

                question_scores.append({
                    'question_title': question.title,
                    'scores': score
                })

            context = {
                'avg_scores': exam_avg_scores,
                'question_scores': question_scores,
            }
            return JsonResponse({'data': context}, status=200)

        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid data type'}, status=400)

# 学生个人中心
@login_required
def profile_student(request):
    student = Student.objects.get(pk=request.user.pk)
    user_id = student.userid
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    # 前端模版渲染内容
    context = {
        'active_page': 'profile',
        'user_id': user_id,
        'notifications': notifications,
        'student': student,
    }
    return render(request, 'profile_student.html', context)

# 学生个人中心-编辑
@login_required
def profile_student_edit(request):
    student = Student.objects.get(pk=request.user.pk)
    user_id = student.userid
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    # 前端模版渲染内容
    context = {
        'active_page': 'profile',
        'user_id': user_id,
        'notifications': notifications,
        'student': student,
    }
    # POST请求时处理提交的个人信息修改
    if request.method == 'POST':
        email = request.POST.get('email')
        student.email = email
        student.save()
        return redirect('student_app:profile_student')
    return render(request, 'profile_student_edit.html', context)

# 学生个人中心-修改密码
@login_required
def profile_student_password(request):
    student = Student.objects.get(pk=request.user.pk)
    user_id = student.userid
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    # 前端模版渲染内容
    context = {
        'active_page': 'profile',
        'user_id': user_id,
        'notifications': notifications,
        'student': student,
    }
    # POST请求时处理提交的密码修改
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        # 检查旧密码是否正确
        if check_password(old_password, student.password):
            if new_password == confirm_password:
                student.password = make_password(new_password)
                student.save()
                return JsonResponse({'status': 'success', 'message': '密码修改成功'}, status=200)
            else:
                return JsonResponse({'status': 'error', 'message': '两次输入的密码不一致'}, status=400)
        else:
            return JsonResponse({'status': 'error', 'message': '旧密码错误'}, status=400)
    return render(request, 'password_student_edit.html', context)

# 通知内容
@login_required
def notification_content(request):
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        notification = Notification.objects.get(id=notification_id)
        return JsonResponse({'title': notification.title, 'content': notification.content}, status=200)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


# 答题界面-班级练习
@login_required
def coding_exercise(request, exercisequestion_id):
    if request.method == 'GET':
        question = get_object_or_404(ExerciseQuestion, id=exercisequestion_id)
        question_set = question.exercise
        # 检查截止时间
        if timezone.now() > question_set.deadline:
            return JsonResponse({'status': 'error', 'message': '截止时间已到，不能作答'}, status=400)
        types = 'exercise'
        return render(request, 'coding_student.html',
                      {'question_set': question_set, 'question': question, 'types': types})
    return render(request, 'coding_student.html')

# 答题界面-班级考试
@login_required
def coding_exam(request, examquestion_id):
    if request.method == 'GET':
        question = get_object_or_404(ExamQuestion, id=examquestion_id)
        question_set = question.exam
        # 检查开始、截止时间
        if timezone.now() < question_set.starttime:
            return JsonResponse({'status': 'error', 'message': '考试尚未开始，不能作答'}, status=400)
        elif timezone.now() > question_set.deadline:
            return JsonResponse({'status': 'error', 'message': '截止时间已到，不能作答'}, status=400)
        types = 'exam'
        return render(request, 'coding_student.html',
                      {'question_set': question_set, 'question': question, 'types': types})
    return render(request, 'coding_student.html')

# 答题界面-年级考试
@login_required
def coding_adminexam(request, examquestion_id):
    student = Student.objects.get(pk=request.user.pk)
    user_id = student.userid
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    # 前端模版渲染内容
    context = {
        'user_id': user_id,
        'notifications': notifications,
    }
    if request.method == 'GET':
        question = get_object_or_404(AdminExamQuestion, id=examquestion_id)
        question_set = question.exam
        # 检查开始、截止时间
        if timezone.now() < question_set.starttime:
            return JsonResponse({'status': 'error', 'message': '考试尚未开始，不能作答'}, status=400)
        elif timezone.now() > question_set.deadline:
            return JsonResponse({'status': 'error', 'message': '截止时间已到，不能作答'}, status=400)
        types = 'adminexam'
        context = {
            'user_id': user_id,
            'notifications': notifications,
            'question_set': question_set,
            'question': question,
            'types': types,
        }
        return render(request, 'coding_student.html', context)
    return render(request, 'coding_student.html', context)

