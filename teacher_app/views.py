import pandas as pd
from datetime import datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseNotFound
from django.contrib.auth.hashers import make_password, check_password

from BERT_app.models import ProgrammingCodeFeature, ProgrammingReportFeature, ReportStandardScore
from BERT_app.views import compute_cosine_similarity
from administrator_app.models import AdminNotification, ProgrammingExercise, AdminExam, AdminExamQuestion
from login.views import login_required
from teacher_app.models import (Teacher, Class, Notification,
                                Exercise, ExerciseQuestion, Exam, ExamQuestion, ReportScore,
                                ExerciseQuestionTestCase, ExamQuestionTestCase)
from student_app.models import (Student, ExerciseCompletion, ExamCompletion, Score,
                                ExerciseQuestionCompletion, ExamQuestionCompletion,
                                AdminExamCompletion, AdminExamQuestionCompletion)
from submissions_app.models import ClassExamSubmission, GradeExamSubmission


# 教师主页
@login_required
def home_teacher(request):
    user_id = request.session.get('user_id')

    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    programing_exercises = ProgrammingExercise.objects.all().order_by('-date_posted')

    context = {
        'user_id': user_id,
        'adminnotifications': adminnotifications,
        'programing_exercises': programing_exercises
    }

    return render(request, 'home_teacher.html', context)


# 教师主页-查看报告
@login_required
def repeat_report(request, programmingexercise_id):
    user_id = request.session.get('user_id')

    teacher = Teacher.objects.get(userid=request.session.get('user_id'))
    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    classes = Class.objects.filter(teacher=teacher)

    context = {
        'user_id': user_id,
        'adminnotifications': adminnotifications,
        'classes': classes,
        'programmingexercise_id': programmingexercise_id
    }
    return render(request, 'similarity_report.html', context)


# 教师主页-查看报告-获取文本数据
@login_required
def repeat_report_details(request, programmingexercise_id):
    user_id = request.session.get('user_id')

    class_id = request.GET.get('class_id')
    students = Student.objects.filter(class_assigned=class_id)
    programmingexercise = ProgrammingExercise.objects.get(id=programmingexercise_id)
    student_similarities = []

    for student in students:
        # 尝试获取当前学生对于特定练习题的编程特征，否则为None
        try:
            student_feature = ProgrammingReportFeature.objects.get(student=student,
                                                                   programming_question=programmingexercise)
        except ProgrammingReportFeature.DoesNotExist:
            student_feature = None

        if student_feature:
            max_similarity = 0
            sim_student = None
            other_features = ProgrammingReportFeature.objects.filter(
                programming_question=programmingexercise).exclude(student=student)
            for other_feature_record in other_features:
                similarity = compute_cosine_similarity(student_feature.feature, other_feature_record.feature)
                if similarity > max_similarity:
                    max_similarity = similarity
                    sim_student = other_feature_record.student
            # 在列表中为当前学生存储最大相似度值和学生对象
            student_similarities.append((student, max_similarity, sim_student))
            # 更新或创建当前学生的余弦相似度记录
            ProgrammingReportFeature.objects.update_or_create(
                student=student,
                programming_question=programmingexercise,
                defaults={'cosine_similarity': max_similarity, 'similar_student': sim_student}
            )
        else:
            # 如果没有学生特征，我们将相似度设置为None
            student_similarities.append((student, None, None))

    teacher = Teacher.objects.get(userid=user_id)
    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    classes = Class.objects.filter(teacher=teacher)

    context = {
        'user_id': user_id,
        'adminnotifications': adminnotifications,
        'classes': classes,
        'programmingexercise_id': programmingexercise_id,
        'students': students,
        'student_similarities': student_similarities,
    }
    return render(request, 'similarity_report_details.html', context)


# 教师主页-查看报告-获取代码数据
@login_required
def repeat_code_details(request, programmingexercise_id):
    user_id = request.session.get('user_id')

    class_id = request.GET.get('class_id')
    students = Student.objects.filter(class_assigned=class_id)
    programmingexercise = ProgrammingExercise.objects.get(id=programmingexercise_id)
    student_similarities = []

    for student in students:
        # 尝试获取当前学生对于特定练习题的编程特征，否则为None
        try:
            student_feature = ProgrammingCodeFeature.objects.get(student=student,
                                                                 programming_question=programmingexercise)
        except ProgrammingCodeFeature.DoesNotExist:
            student_feature = None

        if student_feature:
            max_similarity = 0
            sim_student = None
            other_features = ProgrammingCodeFeature.objects.filter(
                programming_question=programmingexercise).exclude(student=student)
            for other_feature_record in other_features:
                similarity = compute_cosine_similarity(student_feature.feature, other_feature_record.feature)
                if similarity > max_similarity:
                    max_similarity = similarity
                    sim_student = other_feature_record.student
            # 在列表中为当前学生存储最大相似度值和学生对象
            student_similarities.append((student, max_similarity, sim_student))
            # 更新或创建当前学生的余弦相似度记录
            ProgrammingCodeFeature.objects.update_or_create(
                student=student,
                programming_question=programmingexercise,
                defaults={'cosine_similarity': max_similarity, 'similar_student': sim_student}
            )
        else:
            # 如果没有学生特征，将相似度设置为None
            student_similarities.append((student, None, None))

    teacher = Teacher.objects.get(userid=user_id)
    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    classes = Class.objects.filter(teacher=teacher)

    context = {
        'user_id': user_id,
        'adminnotifications': adminnotifications,
        'classes': classes,
        'programmingexercise_id': programmingexercise_id,
        'students': students,
        'student_similarities': student_similarities,
    }
    return render(request, 'similarity_code_details.html', context)


# 教师主页-规范性评分
@login_required
def standard_report(request):
    user_id = request.session.get('user_id')

    teacher = Teacher.objects.get(userid=user_id)
    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    try:
        stand_score = ReportScore.objects.get(teacher=teacher)
    except ObjectDoesNotExist:
        stand_score = None

    if stand_score:
        context = {
            'user_id': user_id,
            'adminnotifications': adminnotifications,
            'stand_score': stand_score,
        }
    else:
        context = {
            'user_id': user_id,
            'adminnotifications': adminnotifications,
        }
    if request.method == 'POST':
        totalscore = request.POST.get('totalscore')
        contents = request.POST.get('contents')
        firstrow = request.POST.get('firstrow')
        fontsize = request.POST.get('fontsize')
        image = request.POST.get('image')
        pagenum = request.POST.get('pagenum')

        ReportScore.objects.update_or_create(
            teacher=teacher,
            defaults={
                'totalscore': totalscore,
                'contents': contents,
                'firstrow': firstrow,
                'fontsize': fontsize,
                'image': image,
                'pagenum': pagenum,
            }
        )
        return redirect('teacher_app:standard_report')

    return render(request, 'standard_report.html', context)


# 教师主页-查看报告-得分详情
@login_required
def scores_details(request, programmingexercise_id):
    user_id = request.session.get('user_id')

    # 获取特定编程题目，班级所有学生的代码规范性得分
    teacher = Teacher.objects.get(userid=user_id)
    classes = Class.objects.filter(teacher=teacher)
    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')

    class_id = request.GET.get('class_id')
    students = Student.objects.filter(class_assigned=class_id)
    programmingexercise = ProgrammingExercise.objects.get(id=programmingexercise_id)
    student_scores = []

    for student in students:
        try:
            report_score = ReportStandardScore.objects.get(student=student, programming_question=programmingexercise)
        except ReportStandardScore.DoesNotExist:
            report_score = None
        student_scores.append((student, report_score))

    context = {
        'student_scores': student_scores,
        'user_id': user_id,
        'classes': classes,
        'adminnotifications': adminnotifications,
        'programmingexercise_id': programmingexercise_id,
    }
    return render(request, 'scores_details.html', context)


# 考试实况
@login_required
def test_check_process(request):
    user_id = request.session.get('user_id')

    teacher = Teacher.objects.get(userid=user_id)
    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')

    # 获取 exam_type 和 exam_id 参数
    exam_type = request.GET.get('exam_type')
    exam_id = request.GET.get('exam_id')
    selected_exam = None
    submissions = []

    if exam_type and exam_id:
        if exam_type == 'adminexam':
            selected_exam = AdminExam.objects.filter(id=exam_id).first()
            submissions = GradeExamSubmission.objects.filter(exam=selected_exam).order_by('-submission_time')
        elif exam_type == 'classexam':
            selected_exam = Exam.objects.filter(id=exam_id, teacher=teacher).first()
            submissions = ClassExamSubmission.objects.filter(exam=selected_exam).order_by('-submission_time')

    context = {
        'user_id': user_id,
        'adminnotifications': adminnotifications,
        'selected_exam': selected_exam,
        'submissions': submissions,
        'exam_type': exam_type,
        'exam_id': exam_id,
    }
    return render(request, 'test_check_process.html', context)


# 考试实况-获取考试项目
@login_required
def get_exam_names(request):
    exam_type = request.GET.get('exam_type')
    user_id = request.session.get('user_id')
    teacher = Teacher.objects.get(userid=user_id)

    if exam_type == 'adminexam':
        exams = AdminExam.objects.all()
    elif exam_type == 'classexam':
        exams = Exam.objects.filter(teacher=teacher)
    else:
        exams = []

    exam_names = [{'id': exam.id, 'name': exam.title} for exam in exams]
    return JsonResponse({'exam_names': exam_names})


# 作业情况
@login_required
def coursework_exercise(request):
    user_id = request.session.get('user_id')

    Exercise.objects.filter(title="默认标题").delete()

    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    teacher = Teacher.objects.get(userid=user_id)
    exercises = Exercise.objects.filter(teacher=teacher).order_by('-published_at')
    classes = Class.objects.filter(teacher=teacher)

    context = {
        'user_id': user_id,
        'coursework': exercises,
        'classes': classes,
        'adminnotifications': adminnotifications
    }

    return render(request, 'coursework_exercise.html', context)


@login_required
def coursework_exam(request):
    user_id = request.session.get('user_id')

    Exam.objects.filter(title="默认标题").delete()

    teacher = Teacher.objects.get(userid=user_id)
    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    exams = Exam.objects.filter(teacher=teacher).order_by('-starttime')
    classes = Class.objects.filter(teacher=teacher)

    context = {
        'user_id': user_id,
        'coursework': exams,
        'classes': classes,
        'adminnotifications': adminnotifications
    }

    return render(request, 'coursework_exam.html', context)


@login_required
def coursework_adminexam(request):
    user_id = request.session.get('user_id')

    AdminExam.objects.filter(title="默认标题").delete()

    teacher = Teacher.objects.get(userid=user_id)
    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    exams = AdminExam.objects.all().order_by('-starttime')
    classes = Class.objects.filter(teacher=teacher)

    context = {
        'user_id': user_id,
        'coursework': exams,
        'classes': classes,
        'adminnotifications': adminnotifications
    }

    return render(request, 'coursework_adminexam.html', context)


# 作业情况：获取数据
@login_required
def coursework_data(request):
    user_id = request.session.get('user_id')

    teacher = Teacher.objects.get(userid=user_id)

    if request.method == 'POST':
        data_type = request.POST.get('type')
        item_id = request.POST.get('id')
        response_data = []

        if data_type == 'exercise':
            exercise = get_object_or_404(Exercise, id=item_id)
            related_classes = exercise.classes.all()
        elif data_type == 'exam':
            exam = get_object_or_404(Exam, id=item_id)
            related_classes = exam.classes.all()
        elif data_type == 'adminexam':
            adminexam = get_object_or_404(AdminExam, id=item_id)
            related_classes = Class.objects.filter(teacher=teacher)
        else:
            return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)

        for class_group in related_classes:
            students = class_group.students.all()
            total_students = students.count()
            student_ids = students.values_list('id', flat=True)

            if total_students > 0:
                if data_type == 'exercise':
                    completed_count = ExerciseCompletion.objects.filter(exercise=exercise, student_id__in=student_ids).count()
                elif data_type == 'exam':
                    completed_count = ExamCompletion.objects.filter(exam=exam, student_id__in=student_ids).count()
                elif data_type == 'adminexam':
                    completed_count = AdminExamCompletion.objects.filter(adminexam=adminexam, student_id__in=student_ids).count()

                completion_rate = (completed_count / total_students)
                response_data.append({
                    'class_name': class_group.name,
                    'completion_rate': completion_rate
                })
            else:
                response_data.append({
                    'class_name': class_group.name,
                    'completion_rate': 0
                })

        return JsonResponse({'data': response_data}, status=200)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


# 作业情况：练习详情
@login_required
def coursework_exercise_details(request, class_id):
    user_id = request.session.get('user_id')

    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    if request.method == 'GET':
        try:
            class_item = Class.objects.get(id=class_id)
            exercises = Exercise.objects.filter(classes=class_item).order_by('-published_at')

            context = {
                'user_id': user_id,
                'coursework': exercises,
                'class_id': class_id,
                'adminnotifications': adminnotifications
            }
            return render(request, 'coursework_exercise_details.html', context)
        except (Class.DoesNotExist, Exercise.DoesNotExist) as e:
            return HttpResponseNotFound('所请求的数据不存在')


# 作业情况：考试详情
@login_required
def coursework_exam_details(request, class_id):
    user_id = request.session.get('user_id')

    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    if request.method == 'GET':
        try:
            class_item = Class.objects.get(id=class_id)
            exams = Exam.objects.filter(classes=class_item).order_by('-starttime')

            context = {
                'user_id': user_id,
                'coursework': exams,
                'class_id': class_id,
                'adminnotifications': adminnotifications
            }
            return render(request, 'coursework_exam_details.html', context)
        except (Class.DoesNotExist, Exercise.DoesNotExist) as e:
            return HttpResponseNotFound('所请求的数据不存在')


# 作业情况：年级考试详情
@login_required
def coursework_adminexam_details(request, class_id):
    user_id = request.session.get('user_id')

    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    if request.method == 'GET':
        try:
            adminexams = AdminExam.objects.all().order_by('-starttime')

            context = {
                'user_id': user_id,
                'coursework': adminexams,
                'class_id': class_id,
                'adminnotifications': adminnotifications
            }
            return render(request, 'coursework_adminexam_details.html', context)
        except (Class.DoesNotExist, Exercise.DoesNotExist) as e:
            return HttpResponseNotFound('所请求的数据不存在')


# 作业情况-详情界面：获取数据
@login_required
def coursework_details_data(request):

    if request.method == 'POST':
        data_type = request.POST.get('type')
        item_id = request.POST.get('id')
        class_item = get_object_or_404(Class, id=request.POST.get('class_id'))
        students = class_item.students.all()
        total_students = students.count()
        student_ids = students.values_list('id', flat=True)
        student_scores_data = []

        if data_type == 'exercise':
            exercise = get_object_or_404(Exercise, id=item_id)
            questions = ExerciseQuestion.objects.filter(exercise=exercise)
            exercisequestion_data = []

            for question in questions:
                question_completed_count = ExerciseQuestionCompletion.objects.filter(
                    exercise=exercise,
                    exercise_question=question,
                    student_id__in=student_ids).count()
                question_completion_rate = (question_completed_count / total_students) \
                    if total_students > 0 else 0
                exercisequestion_data.append({
                    'question_title': question.title,
                    'completion_rate': question_completion_rate,
                })

            # 一次性查询出所有学生的总分数据
            students_scores = Score.objects.filter(
                exercise=exercise,
                # exercise_question__exercise=exercise,
                student__in=students
            ).values('student').annotate(total_score=Sum('score'))
            # 转换查询结果为字典，通过学生ID索引总分
            student_scores_dict = {score['student']: score['total_score'] for score in students_scores}
            # 构造每个学生的得分数据
            for student in students:
                student_total_score = student_scores_dict.get(student.id, 0)  # 获取学生总分，默认为0
                student_scores_data.append({
                    'name': student.name,
                    'userid': student.userid,
                    'total_score': student_total_score
                })

            context = {
                'exercisequestion_data': exercisequestion_data,
                'student_scores_data': student_scores_data
            }
            return JsonResponse({'data': context})

        elif data_type == 'exam':
            exam = get_object_or_404(Exam, id=item_id)
            questions = ExamQuestion.objects.filter(exam=exam)
            examquestion_data = []

            for question in questions:
                question_completed_count = ExamQuestionCompletion.objects.filter(
                    exam=exam,
                    exam_question=question,
                    student_id__in=student_ids).count()
                question_completion_rate = (question_completed_count / total_students) \
                    if total_students > 0 else 0
                examquestion_data.append({
                    'question_title': question.title,
                    'completion_rate': question_completion_rate
                })

            # 一次性查询出所有学生的总分数据
            students_scores = Score.objects.filter(
                exam=exam,
                # exam_question__exam=exam,
                student__in=students
            ).values('student').annotate(total_score=Sum('score'))
            # 转换查询结果为字典，通过学生ID索引总分
            student_scores_dict = {score['student']: score['total_score'] for score in students_scores}
            # 构造每个学生的得分数据
            for student in students:
                student_total_score = student_scores_dict.get(student.id, 0)  # 获取学生总分，默认为0
                student_scores_data.append({
                    'name': student.name,
                    'userid': student.userid,
                    'total_score': student_total_score
                })

            context = {
                'examquestion_data': examquestion_data,
                'student_scores_data': student_scores_data
            }
            return JsonResponse({'data': context})

        elif data_type == 'adminexam':
            adminexam = get_object_or_404(AdminExam, id=item_id)
            questions = AdminExamQuestion.objects.filter(exam=adminexam)
            adminexamquestion_data = []

            for question in questions:
                question_completed_count = AdminExamQuestionCompletion.objects.filter(
                    adminexam=adminexam,
                    adminexam_question=question,
                    student_id__in=student_ids).count()
                question_completion_rate = (question_completed_count / total_students) \
                    if total_students > 0 else 0
                adminexamquestion_data.append({
                    'question_title': question.title,
                    'completion_rate': question_completion_rate
                })

            # 一次性查询出所有学生的总分数据
            students_scores = Score.objects.filter(
                adminexam=adminexam,
                # adminexam_question__exam=adminexam,
                student__in=students
            ).values('student').annotate(total_score=Sum('score'))
            # 转换查询结果为字典，通过学生ID索引总分
            student_scores_dict = {score['student']: score['total_score'] for score in students_scores}
            # 构造每个学生的得分数据
            for student in students:
                student_total_score = student_scores_dict.get(student.id, 0)  # 获取学生总分，默认为0
                student_scores_data.append({
                    'name': student.name,
                    'userid': student.userid,
                    'total_score': student_total_score
                })

            context = {
                'adminexamquestion_data': adminexamquestion_data,
                'student_scores_data': student_scores_data
            }
            return JsonResponse({'data': context})


# 题库管理
@login_required
def repository_teacher(request):
    user_id = request.session.get('user_id')

    teacher = Teacher.objects.get(userid=user_id)
    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')

    Exercise.objects.filter(title="默认标题").delete()
    Exam.objects.filter(title="默认标题").delete()
    exercises = Exercise.objects.filter(teacher=teacher).order_by('-published_at')
    exams = Exam.objects.filter(teacher=teacher).order_by('-starttime')

    context = {
        'user_id': user_id,
        'exercises': exercises,
        'exams': exams,
        'adminnotifications': adminnotifications
    }
    return render(request, 'repository_teacher.html', context)


# 题库管理：练习列表
@login_required
def exercise_list_default(request):
    user_id = request.session.get('user_id')

    teacher = Teacher.objects.get(userid=user_id)
    classes = Class.objects.filter(teacher=teacher)

    exercise = Exercise.objects.create(
        title="默认标题",
        content="默认内容",
        deadline=datetime.now() + timedelta(days=7),
        teacher=teacher
    )

    return render(request, 'exercise_list.html',
                  {'classes': classes, 'exercise': exercise})


@login_required
def exercise_list(request, exercise_id):
    user_id = request.session.get('user_id')

    teacher = Teacher.objects.get(userid=user_id)
    classes = Class.objects.filter(teacher=teacher)
    exercise = get_object_or_404(Exercise, id=exercise_id)

    if request.method == 'POST':
        exercise.title = request.POST.get('title')
        exercise.content = request.POST.get('content')
        exercise.published_at = datetime.now()
        exercise.deadline = request.POST.get('deadline')

        recipient_ids = request.POST.get('recipients').split(',')
        recipient_class = Class.objects.filter(id__in=recipient_ids)
        if recipient_class:
            exercise.save()
            exercise.classes.set(recipient_class)
            return redirect('teacher_app:repository_teacher')
    return render(request, 'exercise_list.html',
                  {'classes': classes, 'exercise': exercise})


# 题库管理：练习列表-创建练习
@login_required
def create_exercise(request, exercise_id):

    exercise = get_object_or_404(Exercise, id=exercise_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        memory_limit = request.POST.get('memory_limit')
        time_limit = request.POST.get('time_limit')

        question = ExerciseQuestion(exercise=exercise, title=title, content=content,
                                    memory_limit=memory_limit, time_limit=time_limit)
        question.save()

        # 遍历提交的测试用例
        for key in request.POST.keys():
            if key.startswith('input'):
                testcase_num = key[5:]  # 获取测试用例的编号
                input_data = request.POST.get('input' + testcase_num)
                output_data = request.POST.get('output' + testcase_num)

                # 创建一个新的ExerciseQuestionTestCase实例
                testcase = ExerciseQuestionTestCase(question=question, input=input_data, expected_output=output_data)
                testcase.save()

        return redirect('teacher_app:exercise_list', exercise_id=exercise.id)
    return render(request, 'create_exercise.html', {'exercise': exercise})


# 题库管理：练习列表-修改练习题
@login_required
def exercise_edit(request, exercise_id):

    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    if request.method == 'GET':
        exercise = Exercise.objects.get(id=exercise_id)
        context = {
            'exercise': exercise,
            'adminnotifications': adminnotifications
        }
        return render(request, 'exercise_edit.html', context)


# 题库管理：练习列表-删除练习
@login_required
def exercise_delete(request):

    if request.method == 'POST':
        exercise_id = request.POST.get('exercise_id')
        if exercise_id:
            exercise_to_delete = Exercise.objects.filter(id=exercise_id).first()
            if exercise_to_delete:
                exercise_to_delete.questions.all().delete()
                exercise_to_delete.classes.clear()
                exercise_to_delete.delete()
                return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': '练习未找到'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


# 题库管理：练习列表-删除练习题
@login_required
def exercisequestion_delete(request):

    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        if question_id:
            question_to_delete = ExerciseQuestion.objects.filter(id=question_id).first()
            if question_to_delete:
                question_to_delete.delete()
                return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': '练习题未找到'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


# 题库管理：考试列表
@login_required
def exam_list_default(request):
    user_id = request.session.get('user_id')

    teacher = Teacher.objects.get(userid=user_id)
    classes = Class.objects.filter(teacher=teacher)

    exam = Exam.objects.create(
        title="默认标题",
        content="默认内容",
        starttime=datetime.now(),
        deadline=datetime.now() + timedelta(days=7),
        teacher=teacher
    )

    return render(request, 'exam_list.html',
                  {'classes': classes, 'exam': exam})


@login_required
def exam_list(request, exam_id):
    user_id = request.session.get('user_id')

    teacher = Teacher.objects.get(userid=user_id)
    classes = Class.objects.filter(teacher=teacher)
    exam = get_object_or_404(Exam, id=exam_id)

    if request.method == 'POST':
        exam.title = request.POST.get('title')
        exam.content = request.POST.get('content')
        exam.starttime = request.POST.get('starttime')
        exam.deadline = request.POST.get('deadline')

        recipient_ids = request.POST.get('recipients').split(',')
        recipient_class = Class.objects.filter(id__in=recipient_ids)
        if recipient_class:
            exam.save()
            exam.classes.set(recipient_class)
            return redirect('teacher_app:repository_teacher')
    return render(request, 'exam_list.html',
                  {'classes': classes, 'exam': exam})


# 题库管理：考试列表-创建考试
@login_required
def create_exam(request, exam_id):

    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        memory_limit = request.POST.get('memory_limit')
        time_limit = request.POST.get('time_limit')

        question = ExamQuestion(exam=exam, title=title, content=content,
                                memory_limit=memory_limit, time_limit=time_limit)
        question.save()

        # 遍历提交的测试用例
        for key in request.POST.keys():
            if key.startswith('input'):
                testcase_num = key[5:]  # 获取测试用例的编号
                input_data = request.POST.get('input' + testcase_num)
                output_data = request.POST.get('output' + testcase_num)

                # 创建一个新的ExamQuestionTestCase实例
                testcase = ExamQuestionTestCase(question=question, input=input_data, expected_output=output_data)
                testcase.save()

        return redirect('teacher_app:exam_list', exam_id=exam.id)
    return render(request, 'create_exam.html', {'exam': exam})


# 题库管理：考试列表-修改考试题
@login_required
def exam_edit(request, exam_id):

    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    if request.method == 'GET':
        exam = Exam.objects.get(id=exam_id)
        context = {
            'exam': exam,
            'adminnotifications': adminnotifications
        }
        return render(request, 'exam_edit.html', context)


# 题库管理：考试列表-删除考试
@login_required
def exam_delete(request):

    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        if exam_id:
            exam_to_delete = Exam.objects.filter(id=exam_id).first()
            if exam_to_delete:
                exam_to_delete.questions.all().delete()
                exam_to_delete.classes.clear()
                exam_to_delete.delete()
                return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': '考试未找到'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


# 题库管理：考试列表-删除考试题
@login_required
def examquestion_delete(request):

    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        if question_id:
            question_to_delete = ExamQuestion.objects.filter(id=question_id).first()
            if question_to_delete:
                question_to_delete.delete()
                return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': '考试题未找到'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


# 通知界面
@login_required
def notice_teacher(request):
    user_id = request.session.get('user_id')

    teacher = Teacher.objects.get(userid=user_id)
    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    classes = Class.objects.filter(teacher=teacher)
    notifications = Notification.objects.filter(recipients__in=classes).order_by('-date_posted').distinct()

    context = {
        'user_id': user_id,
        'notifications': notifications,
        'adminnotifications': adminnotifications
    }
    return render(request, 'notice_teacher.html', context)


# 发布通知
@login_required
def create_notice(request):
    user_id = request.session.get('user_id')

    teacher = Teacher.objects.get(userid=user_id)
    classes = Class.objects.filter(teacher=teacher)

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('message')
        recipient_ids = request.POST.get('recipients').split(',')
        recipients = Class.objects.filter(id__in=recipient_ids)

        if title and content and recipients:
            notification = Notification(title=title, content=content)
            notification.save()
            notification.recipients.set(recipients)
        return redirect('teacher_app:notice_teacher')
    return render(request, 'create_notice.html',
                  {'user_id': user_id, 'classes': classes})


# 删除通知
@login_required
def delete_notice(request):

    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        if notification_id:
            notification_to_delete = Notification.objects.filter(id=notification_id).first()
            if notification_to_delete:
                notification_to_delete.delete()
                return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': '通知未找到'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


# 通知详情
@login_required
def notification_content(request):

    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        notification = Notification.objects.get(id=notification_id)
        return JsonResponse({'title': notification.title, 'content': notification.content})
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


# 班级管理
@login_required
def class_teacher(request):
    user_id = request.session.get('user_id')

    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    teacher = Teacher.objects.get(userid=user_id)
    classes = Class.objects.filter(teacher=teacher)

    context = {
        'classes': classes,
        'user_id': user_id,
        'adminnotifications': adminnotifications
    }
    return render(request, 'class_teacher.html', context)


# 班级管理：创建班级
@login_required
def create_class(request):
    user_id = request.session.get('user_id')

    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    context = {
        'user_id': user_id,
        'adminnotifications': adminnotifications
    }
    if request.method == 'POST':
        class_name = request.POST.get('className')
        initial_password = request.POST.get('initialPassword')
        file = request.FILES.get('excelFile')

        if class_name and initial_password and file:
            teacher = Teacher.objects.get(userid=request.session.get('user_id'))
            new_class = Class.objects.create(name=class_name, teacher=teacher)

            data = pd.read_excel(file)
            for index, row in data.iterrows():
                hashed_password = make_password(initial_password)
                Student.objects.create(
                    name=row['姓名'],
                    userid=row['学号'],
                    password=hashed_password,
                    class_assigned=new_class
                )
            return redirect('teacher_app:class_teacher')
    return render(request, 'create_class.html', context)


# 班级管理：删除班级
@login_required
def delete_class(request):

    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        if class_id:
            class_to_delete = Class.objects.filter(id=class_id)
            class_to_delete.delete()
            return JsonResponse({'status': 'success', 'message': '班级删除成功'}, status=200)
        return JsonResponse({'status': 'error', 'message': '班级未找到'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


# 班级管理：班级详情
@login_required
def class_details(request, class_id):
    user_id = request.session.get('user_id')

    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')
    if request.method == 'GET':
        try:
            students = Student.objects.filter(class_assigned=class_id)
            context = {
                'students': students,
                'user_id': user_id,
                'adminnotifications': adminnotifications
            }
            return render(request, 'class_details.html', context)
        except Class.DoesNotExist:
            return redirect('teacher_app:class_teacher')
    else:
        messages.error(request, '无效的请求方法')
        return redirect('teacher_app:class_teacher')


# 班级管理：删除学生
@login_required
def delete_student(request):

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        try:
            student_to_delete = Student.objects.get(id=student_id)
            student_to_delete.class_assigned = None
            student_to_delete.save()
            student_to_delete.delete()
            return JsonResponse({'status': 'success', 'message': '删除成功'})
        except Student.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '学生用户不存在'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


# 班级管理：初始化密码
@login_required
def reset_password(request):

    if request.method == 'POST':
        student = Student.objects.get(id=request.POST.get('student_id'))
        try:
            initial_password = 'cumt1909'  # 设置为默认密码
            hashed_password = make_password(initial_password)
            student.password = hashed_password
            student.save()
            return JsonResponse({'status': 'success', 'message': '初始化成功，密码改为cumt1909'}, status=200)
        except Student.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '初始化密码失败'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)


# 教师个人中心
@login_required
def profile_teacher(request):
    user_id = request.session.get('user_id')

    teacher = Teacher.objects.get(userid=request.session.get('user_id'))
    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')

    context = {
        'user_id': user_id,
        'teacher': teacher,
        'adminnotifications': adminnotifications
    }
    return render(request, 'profile_teacher.html', context)


# 教师个人中心-编辑
@login_required
def profile_teacher_edit(request):
    user_id = request.session.get('user_id')

    teacher = Teacher.objects.get(userid=user_id)
    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')

    context = {
        'user_id': user_id,
        'teacher': teacher,
        'adminnotifications': adminnotifications
    }

    if request.method == 'POST':
        phone_num = request.POST.get('phone_num')
        email = request.POST.get('email')
        teacher.phone_num = phone_num
        teacher.email = email
        teacher.save()
        return redirect('teacher_app:profile_teacher')

    return render(request, 'profile_teacher_edit.html', context)


# 教师个人中心-修改密码
@login_required
def profile_teacher_password(request):
    user_id = request.session.get('user_id')

    teacher = Teacher.objects.get(userid=user_id)
    adminnotifications = AdminNotification.objects.all().order_by('-date_posted')

    context = {
        'user_id': user_id,
        'teacher': teacher,
        'adminnotifications': adminnotifications
    }

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if check_password(old_password, teacher.password):
            if new_password == confirm_password:
                teacher.password = make_password(new_password)
                teacher.save()
                return JsonResponse({'status': 'success', 'message': '密码修改成功'})
            else:
                return JsonResponse({'status': 'error', 'message': '两次输入的密码不一致'}, status=400)
        else:
            return JsonResponse({'status': 'error', 'message': '旧密码错误'}, status=400)
    return render(request, 'password_teacher_edit.html', context)




