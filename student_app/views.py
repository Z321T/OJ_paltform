import os
import docx
import time
import tempfile
from io import BytesIO

from django.utils import timezone
from django.db.models import Sum
from django.forms.models import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import make_password, check_password

from administrator_app.models import ProgrammingExercise, AdminExam, AdminExamQuestion
from student_app.models import (Student, Score, ExerciseCompletion, ExerciseQuestionCompletion,
                                StudentCode, TestResult,
                                ExamCompletion, ExamQuestionCompletion,
                                AdminExamCompletion, AdminExamQuestionCompletion)
from teacher_app.models import Notification, Exercise, Exam, ExerciseQuestion, ExamQuestion, ReportScore
from BERT_app.views import (analyze_programming_report,
                            score_report, analyze_programming_code)
from login.views import login_required


# 学生主页
@login_required
def home_student(request):
    user_id = request.session.get('user_id')

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
@login_required
def report_student(request, programmingexercise_id):
    user_id = request.session.get('user_id')

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

    # 检查截止时间
    if timezone.now() > programming_exercise.deadline:
        return JsonResponse({'status': 'error', 'message': '截止时间已到，不能提交报告'})

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
@login_required
def practice_student(request):
    user_id = request.session.get('user_id')

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
@login_required
def practice_list(request, exercise_id):
    user_id = request.session.get('user_id')

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
@login_required
def exam_student(request):
    user_id = request.session.get('user_id')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    class_assigned = student.class_assigned

    th_exams = Exam.objects.filter(classes=class_assigned).order_by('-starttime')
    admin_exams = AdminExam.objects.filter(classes=class_assigned).order_by('-starttime')

    context = {
        'user_id': user_id,
        'th_exams': th_exams,
        'admin_exams': admin_exams,
        'notifications': notifications,
    }
    return render(request, 'exam_student.html', context)


# 我的考试：教师考试详情
@login_required
def teacherexam_list(request, exam_id):
    user_id = request.session.get('user_id')

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
@login_required
def adminexam_list(request, exam_id):
    user_id = request.session.get('user_id')

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
@login_required
def analyse_exercise(request):
    user_id = request.session.get('user_id')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    exercises = Exercise.objects.filter(classes=student.class_assigned).order_by('-published_at')

    context = {
        'user_id': user_id,
        'notifications': notifications,
        'coursework': exercises,
    }
    return render(request, 'analyse_exercise.html', context)


@login_required
def analyse_exam(request):
    user_id = request.session.get('user_id')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')
    exams = Exam.objects.filter(classes=student.class_assigned).order_by('-starttime')

    context = {
        'user_id': user_id,
        'notifications': notifications,
        'coursework': exams,
    }
    return render(request, 'analyse_exam.html', context)


@login_required
def analyse_data(request):
    user_id = request.session.get('user_id')

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
@login_required
def profile_student(request):
    user_id = request.session.get('user_id')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')

    context = {
        'user_id': user_id,
        'notifications': notifications,
        'student': student,
    }

    return render(request, 'profile_student.html', context)


# 学生个人中心-编辑
@login_required
def profile_student_edit(request):
    user_id = request.session.get('user_id')

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
@login_required
def profile_student_password(request):
    user_id = request.session.get('user_id')

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
@login_required
def notification_content(request):
    user_id = request.session.get('user_id')

    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        notification = Notification.objects.get(id=notification_id)
        return JsonResponse({'title': notification.title, 'content': notification.content})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


# 答题界面
@login_required
def coding_exercise(request, exercisequestion_id):
    user_id = request.session.get('user_id')

    if request.method == 'GET':
        question = get_object_or_404(ExerciseQuestion, id=exercisequestion_id)
        question_set = question.exercise

        # 检查截止时间
        if timezone.now() > question_set.deadline:
            return JsonResponse({'status': 'error', 'message': '截止时间已到，不能作答'})

        types = 'exercise'
        return render(request, 'coding_student.html',
                      {'question_set': question_set, 'question': question, 'types': types})
    return render(request, 'coding_student.html')


@login_required
def coding_exam(request, examquestion_id):
    user_id = request.session.get('user_id')

    if request.method == 'GET':
        question = get_object_or_404(ExamQuestion, id=examquestion_id)
        question_set = question.exam

        # 检查开始、截止时间
        if timezone.now() < question_set.starttime:
            return JsonResponse({'status': 'error', 'message': '考试尚未开始，不能作答'})
        elif timezone.now() > question_set.deadline:
            return JsonResponse({'status': 'error', 'message': '截止时间已到，不能作答'})

        types = 'exam'
        return render(request, 'coding_student.html',
                      {'question_set': question_set, 'question': question, 'types': types})
    return render(request, 'coding_student.html')


@login_required
def coding_adminexam(request, examquestion_id):
    user_id = request.session.get('user_id')

    student = Student.objects.get(userid=user_id)
    notifications = Notification.objects.filter(recipients=student.class_assigned).order_by('-date_posted')

    context = {
        'user_id': user_id,
        'notifications': notifications,
    }

    if request.method == 'GET':
        question = get_object_or_404(AdminExamQuestion, id=examquestion_id)
        question_set = question.exam

        # 检查开始、截止时间
        if timezone.now() < question_set.starttime:
            return JsonResponse({'status': 'error', 'message': '考试尚未开始，不能作答'})
        elif timezone.now() > question_set.deadline:
            return JsonResponse({'status': 'error', 'message': '截止时间已到，不能作答'})

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
@login_required
def run_cpp_code(request):
    user_id = request.session.get('user_id')

    student = Student.objects.get(userid=user_id)
    if request.method == 'POST':
        user_code = request.POST.get('code', '')  # 从表单数据中获取代码
        types = request.POST.get('types', '')  # 从表单数据中获取题目类型
        question_id = request.POST.get('questionId', '')  # 从表单数据中获取题目id

        # 检查是否在截止时间之前提交代码
        if types == 'exercise':
            question = ExerciseQuestion.objects.get(id=question_id)
            exercise = question.exercise
            if timezone.now() > exercise.deadline:
                return JsonResponse({'status': 'error', 'message': '截止时间已到，不能提交'})

        elif types == 'exam':
            question = ExamQuestion.objects.get(id=question_id)
            exam = question.exam
            if timezone.now() > exam.deadline:
                return JsonResponse({'status': 'error', 'message': '截止时间已到，不能提交'})

        elif types == 'adminexam':
            question = AdminExamQuestion.objects.get(id=question_id)
            exam = question.exam
            if timezone.now() > exam.deadline:
                return JsonResponse({'status': 'error', 'message': '截止时间已到，不能提交'})

        StudentCode.objects.update_or_create(
            student=student,
            question_type=types,
            question_id=question_id,
            defaults={'code': user_code},
        )

        result = None
        for _ in range(50):
            try:
                result = TestResult.objects.get(student=student, question_type=types, question_id=question_id)
                if result.status is not None:
                    # 将对象转换为字典
                    result_dict = model_to_dict(result)
                    break
            except ObjectDoesNotExist:
                time.sleep(5)
        if result is None:
            return JsonResponse({'error': '测试出现错误，请重新提交'}, status=400)

        # 获取任务结果
        try:
            if result.status == 'pass':

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
                result.delete()
                return JsonResponse(result_dict)

            elif result.status == 'fail':

                # 测试用例未全部通过的情况
                passed_tests = result.passed_tests
                total_tests = result.testcases
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
                result.delete()
                return JsonResponse(result_dict)

            elif result.status == 'compile error':
                error = result.error
                result.delete()
                # 出现编译错误的情况
                return JsonResponse({'error': error})

        except Exception as e:
            return JsonResponse({'error': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)





