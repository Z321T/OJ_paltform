import os
import docx
import requests
import tempfile
from io import BytesIO

from django.utils import timezone
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.hashers import make_password, check_password

from administrator_app.models import ProgrammingExercise, AdminExam, AdminExamQuestion
from student_app.models import (Student, Score, ExerciseCompletion, ExerciseQuestionCompletion,
                                ExamCompletion, ExamQuestionCompletion,
                                AdminExamCompletion, AdminExamQuestionCompletion)
from teacher_app.models import Notification, Exercise, Exam, ExerciseQuestion, ExamQuestion, ReportScore
from BERT_app.views import (analyze_programming_report,
                            score_report, analyze_programming_code)
from login.views import check_login
from CUMT.task import test_cpp_code
# from celery.result import AsyncResult


# 学生主页
def home_student(request):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    programing_exercises = ProgrammingExercise.objects.all().order_by('-date_posted')

    context = {
        'user_id': user_id,
        'notifications': notifications,
        'programing_exercises': programing_exercises,
    }

    return render(request, 'home_student.html', context)


# 学生主页：提交报告
def report_student(request, programmingexercise_id):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    programming_exercise = get_object_or_404(ProgrammingExercise, id=programmingexercise_id)
    if request.method == 'GET':
        notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')

        context = {
            'user_id': user_id,
            'notifications': notifications,
            'programming_exercise': programming_exercise,
        }
        return render(request, 'report_student.html', context)

    if request.method == 'POST':
        reportstandards = ReportScore.objects.filter(teacher=student.class_assigned.teacher)
        if reportstandards:
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
                # 报告规范性评分
                score_report(student, document, programmingexercise_id)

            # 读取TXT文件内容
            code_file = request.FILES.get('txtFile')
            if code_file:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
                temp_file.write(code_file.read())
                temp_file.close()
                # 分析代码特征
                code = open(temp_file.name, encoding='utf-8').read()
                analyze_programming_code(student, code, programmingexercise_id)
                # 删除临时文件
                os.unlink(temp_file.name)
            return JsonResponse({'status': 'success', 'message': '提交成功'})

        else:
            return JsonResponse({'status': 'error', 'message': '教师未设置报告规范性评分标准'}, status=400)


# 我的练习
def practice_student(request):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    class_assigned = student.class_assigned
    exercises = Exercise.objects.filter(classes=class_assigned).order_by('-published_at')

    context = {
        'user_id': user_id,
        'exercises': exercises,
        'notifications': notifications,
    }
    return render(request, 'practice_student.html', context)


# 我的练习：练习详情
def practice_list(request, exercise_id):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    if request.method == 'GET':
        exercise = Exercise.objects.get(id=exercise_id)

        context = {
            'user_id': user_id,
            'exercise': exercise,
            'notifications': notifications,
        }
        return render(request, 'practice_list.html', context)


# 我的考试
def exam_student(request):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    class_assigned = student.class_assigned

    th_exams = Exam.objects.filter(classes=class_assigned).order_by('-published_at')
    admin_exams = AdminExam.objects.filter(classes=class_assigned).order_by('-published_at')

    context = {
        'user_id': user_id,
        'th_exams': th_exams,
        'admin_exams': admin_exams,
        'notifications': notifications,
    }
    return render(request, 'exam_student.html', context)


# 我的考试：教师考试详情
def teacherexam_list(request, exam_id):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    if request.method == 'GET':
        exam = Exam.objects.get(id=exam_id)

        context = {
            'user_id': user_id,
            'exam': exam,
            'notifications': notifications,
        }
        return render(request, 'teacherexam_list.html', context)


# 我的考试：管理员考试详情
def adminexam_list(request, exam_id):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    if request.method == 'GET':
        exam = AdminExam.objects.get(id=exam_id)

        context = {
            'user_id': user_id,
            'exam': exam,
            'notifications': notifications,
        }
        return render(request, 'adminexam_list.html', context)


# 学情分析
def analyse_exercise(request):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    exercises = Exercise.objects.filter(classes=student.class_assigned).order_by('-published_at')

    context = {
        'user_id': user_id,
        'notifications': notifications,
        'coursework': exercises,
    }
    return render(request, 'analyse_exercise.html', context)


def analyse_exam(request):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    exams = Exam.objects.filter(classes=student.class_assigned).order_by('-published_at')

    context = {
        'user_id': user_id,
        'notifications': notifications,
        'coursework': exams,
    }
    return render(request, 'analyse_exam.html', context)


def analyse_data(request):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    class_assigned = student.class_assigned
    if request.method == 'POST':
        data_type = request.POST.get('type')
        item_id = request.POST.get('id')

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
                    score_obj = Score.objects.get(student=student, exercise_question=question)
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
            return JsonResponse({'data': context})

        elif data_type == 'exam':
            # 计算每个考试的平均得分
            exam = Exam.objects.filter(classes=class_assigned)
            exam_avg_scores = []
            for ex in exam:
                question_count = ex.questions.count()
                ex_questions = ExamQuestion.objects.filter(exam=ex)
                total_score = Score.objects.filter(
                    student=student,
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
                    score_obj = Score.objects.get(student=student, exam_question=question)
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
            return JsonResponse({'data': context})

        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid data type'}, status=400)


# 学生个人中心
def profile_student(request):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')

    context = {
        'user_id': user_id,
        'notifications': notifications,
        'student': student,
    }

    return render(request, 'profile_student.html', context)


# 学生个人中心-编辑
def profile_student_edit(request):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')

    context = {
        'user_id': user_id,
        'notifications': notifications,
        'student': student,
    }

    if request.method == 'POST':
        email = request.POST.get('email')
        student.email = email
        student.save()
        return redirect('student_app:profile_student')

    return render(request, 'profile_student_edit.html', context)


# 学生个人中心-修改密码
def profile_student_password(request):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')

    context = {
        'user_id': user_id,
        'notifications': notifications,
        'student': student,
    }

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if check_password(old_password, student.password):
            if new_password == confirm_password:
                student.password = make_password(new_password)
                student.save()
                return JsonResponse({'status': 'success', 'message': '密码修改成功'})
            else:
                return JsonResponse({'status': 'error', 'message': '两次输入的密码不一致'}, status=400)
        else:
            return JsonResponse({'status': 'error', 'message': '旧密码错误'}, status=400)
    return render(request, 'password_student_edit.html', context)


# 通知内容
def notification_content(request):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        notification = Notification.objects.get(id=notification_id)
        return JsonResponse({'title': notification.title, 'content': notification.content})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


# 答题界面
def coding_exercise(request, exercisequestion_id):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    if request.method == 'GET':
        question = get_object_or_404(ExerciseQuestion, id=exercisequestion_id)
        question_set = question.exercise
        types = 'exercise'
        return render(request, 'coding_student.html',
                      {'question_set': question_set, 'question': question, 'types': types})
    return render(request, 'coding_student.html')


def coding_exam(request, examquestion_id):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    if request.method == 'GET':
        question = get_object_or_404(ExamQuestion, id=examquestion_id)
        question_set = question.exam
        types = 'exam'
        return render(request, 'coding_student.html',
                      {'question_set': question_set, 'question': question, 'types': types})
    return render(request, 'coding_student.html')


def coding_adminexam(request, examquestion_id):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')

    context = {
        'user_id': user_id,
        'notifications': notifications,
    }

    if request.method == 'GET':
        question = get_object_or_404(AdminExamQuestion, id=examquestion_id)
        question_set = question.exam
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


def call_node_api(request):
    response = requests.get('http://localhost:3000/api')  # Node.js服务器的地址
    return HttpResponse(response.json())


# 标记完成的题目
def mark_exercise_question_as_completed(student, exercise_question):
    ExerciseQuestionCompletion.objects.create(
        student=student,
        exercise_question=exercise_question,
        completed_at=timezone.now()
    )
    # 检查是否所有的练习题都已经完成
    all_questions = exercise_question.exercise.questions.all()
    completed_questions = ExerciseQuestionCompletion.objects.filter(
        student=student,
        exercise_question__in=all_questions
    )
    if all_questions.count() == completed_questions.count():
        ExerciseCompletion.objects.create(
            student=student,
            exercise=exercise_question.exercise,
            completed_at=timezone.now()
        )


def mark_exam_question_as_completed(student, exam_question):
    ExamQuestionCompletion.objects.create(
        student=student,
        exam_question=exam_question,
        completed_at=timezone.now()
    )
    all_questions = exam_question.exam.questions.all()
    completed_questions = ExamQuestionCompletion.objects.filter(
        student=student,
        exam_question__in=all_questions
    )
    if all_questions.count() == completed_questions.count():
        ExamCompletion.objects.create(
            student=student,
            exam=exam_question.exam,
            completed_at=timezone.now()
        )


def mark_adminexam_question_as_completed(student, adminexam_question):
    AdminExamQuestionCompletion.objects.create(
        student=student,
        adminexam_question=adminexam_question,
        completed_at=timezone.now()
    )
    all_questions = adminexam_question.exam.questions.all()
    completed_questions = AdminExamQuestionCompletion.objects.filter(
        student=student,
        adminexam_question__in=all_questions
    )
    if all_questions.count() == completed_questions.count():
        AdminExamCompletion.objects.create(
            student=student,
            adminexam=adminexam_question.exam,
            completed_at=timezone.now()
        )


# 运行C++代码
def run_cpp_code(request):
    user_id = request.session.get('user_id')
    if check_login(user_id):
        return redirect('/login/')

    student = Student.objects.get(userid=user_id)
    if request.method == 'POST':
        print('后端收到代码')
        user_code = request.POST.get('code', '')  # 从表单数据中获取代码
        types = request.POST.get('types', '')  # 从表单数据中获取题目类型
        question_id = request.POST.get('questionId', '')  # 从表单数据中获取题目id

        # 调用 Celery 任务
        # task = test_cpp_code.delay(user_code, types, question_id)
        result = test_cpp_code(user_code, types, question_id)
        print('运行结果', result)
        # # 获取任务的UUID
        # task_id = task.id

        # # 创建一个AsyncResult对象
        # result = AsyncResult(task_id)

        # 获取任务结果
        try:
            result = result.get()
            if result['status'] == 'pass':
                # 测试用例全部通过的情况
                if types == 'exercise':
                    question = ExerciseQuestion.objects.get(id=question_id)
                    mark_exercise_question_as_completed(student, question)
                    Score.objects.update_or_create(
                        student=student,
                        exercise_question=question,
                        defaults={'score': 10}
                    )
                elif types == 'exam':
                    question = ExamQuestion.objects.get(id=question_id)
                    mark_exam_question_as_completed(student, question)
                    Score.objects.update_or_create(
                        student=student,
                        exam_question=question,
                        defaults={'score': 10}
                    )
                else:
                    question = AdminExamQuestion.objects.get(id=question_id)
                    mark_adminexam_question_as_completed(student, question)
                    Score.objects.update_or_create(
                        student=student,
                        adminexam_question=question,
                        defaults={'score': 10}
                    )
                print('返回结果-通过')
                return JsonResponse(result)

            elif result['status'] == 'fail':
                # 测试用例未全部通过的情况
                passed_tests = result['passed_tests']
                total_tests = len(result['tests_results'])
                score = round((passed_tests / total_tests) * 10, 3)

                if types == 'exercise':
                    question = ExerciseQuestion.objects.get(id=question_id)
                    mark_exercise_question_as_completed(student, question)
                    Score.objects.update_or_create(
                        student=student,
                        exercise_question=question,
                        defaults={'score': score}
                    )
                elif types == 'exam':
                    question = ExamQuestion.objects.get(id=question_id)
                    mark_exam_question_as_completed(student, question)
                    Score.objects.update_or_create(
                        student=student,
                        exam_question=question,
                        defaults={'score': score}
                    )
                else:
                    question = AdminExamQuestion.objects.get(id=question_id)
                    mark_adminexam_question_as_completed(student, question)
                    Score.objects.update_or_create(
                        student=student,
                        adminexam_question=question,
                        defaults={'score': score}
                    )
                print('返回结果-未通过')
                return JsonResponse(result)

            elif result['status'] == 'compile error':
                # 出现编译错误的情况
                print('返回结果-编译错误')
                return JsonResponse({'error': result['error']})

        except Exception as e:
            return JsonResponse({'error': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

# def run_cpp_code(request):
#     user_id = request.session.get('user_id')
#     if check_login(user_id):
#         return redirect('/login/')
#
#     student = Student.objects.get(userid=user_id)
#     if request.method == 'POST':
#         user_code = request.POST.get('code', '')  # 从表单数据中获取代码
#         types = request.POST.get('types', '')  # 从表单数据中获取题目类型
#         question_id = request.POST.get('questionId', '')  # 从表单数据中获取题目id
#
#         with open('temp.cpp', 'w') as f:
#             f.write(user_code)
#
#         try:
#             start_time = time.time()  # 记录开始时间
#             result = subprocess.run(
#                 ['docker', 'run', '--rm', '-v', f"{os.getcwd()}:/app",
#                  '-w', '/app', '-m', '512m', '--cpus', '1', 'cpp-runner',
#                  'bash', '-c', 'g++ temp.cpp -o temp && ./temp'],
#                 capture_output=True, text=True, timeout=30
#             )
#             execution_time = time.time() - start_time  # 计算执行时间
#
#             if result.returncode == 0:  # 如果运行成功
#                 if types == 'exercise':
#                     question = ExerciseQuestion.objects.get(id=question_id)
#                 elif types == 'exam':
#                     question = ExamQuestion.objects.get(id=question_id)
#                 else:
#                     question = AdminExamQuestion.objects.get(id=question_id)
#                 if question.answer == result.stdout:
#                     if types == 'exercise':
#                         mark_exercise_question_as_completed(student, question)
#                         Score.objects.update_or_create(
#                             student=student,
#                             exercise_question=question,
#                             defaults={'score': 10}
#                         )
#                     elif types == 'exam':
#                         mark_exam_question_as_completed(student, question)
#                         Score.objects.update_or_create(
#                             student=student,
#                             exam_question=question,
#                             defaults={'score': 10}
#                         )
#                     else:
#                         mark_adminexam_question_as_completed(student, question)
#                         Score.objects.update_or_create(
#                             student=student,
#                             adminexam_question=question,
#                             defaults={'score': 10}
#                         )
#                     # 这里仅返回了执行结果和时间，与前端代码对应
#                     return JsonResponse({'status': 'success', 'message': '题目作答正确',
#                                          'output': result.stdout, 'time': execution_time})
#                 else:
#                     return JsonResponse({'output': result.stdout, 'error': 'Wrong answer', 'time': execution_time})
#             else:  # 如果编译或运行出错
#                 return JsonResponse({'error': result.stderr, 'time': execution_time})
#         except subprocess.TimeoutExpired:  # 如果运行超时
#             return JsonResponse({'error': 'Execution timed out'})
#         except Exception as e:  # 如果发生其他异常
#             return JsonResponse({'error': str(e)})
#     else:
#         return JsonResponse({'error': 'Invalid request'}, status=400)



