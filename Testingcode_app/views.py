import time

from django.http import JsonResponse
from django.utils import timezone

from django_q.tasks import async_task
from django_q.models import Task

from Testingcode_app.models import ExerciseQuestionCompletion, ExerciseCompletion, ExamQuestionCompletion, \
    ExamCompletion, AdminExamQuestionCompletion, AdminExamCompletion, StudentCode, TestResult, Score
from administrator_app.models import AdminExamQuestion
from student_app.models import Student
from teacher_app.models import ExerciseQuestion, ExamQuestion

# Create your views here.
# 标记完成的班级练习题目
def mark_exercise_question_as_completed(student, exercise, exercise_question):
    ExerciseQuestionCompletion.objects.update_or_create(
        student=student,
        exercise=exercise,
        exercise_question=exercise_question,
        defaults={
            'completed_at': timezone.now()
        }
    )
    # 检查是否所有的练习题都已经完成
    all_questions = exercise_question.exercise.questions.all()
    completed_questions = ExerciseQuestionCompletion.objects.filter(
        student=student,
        exercise=exercise,
        exercise_question__in=all_questions
    )
    if all_questions.count() == completed_questions.count():
        ExerciseCompletion.objects.update_or_create(
            student=student,
            exercise=exercise,
            defaults={
                'completed_at': timezone.now()
            }
        )

# 标记完成的班级考试题目
def mark_exam_question_as_completed(student, exam, exam_question):
    ExamQuestionCompletion.objects.update_or_create(
        student=student,
        exam=exam,
        exam_question=exam_question,
        defaults={
            'completed_at': timezone.now()
        }
    )
    all_questions = exam_question.exam.questions.all()
    completed_questions = ExamQuestionCompletion.objects.filter(
        student=student,
        exam=exam,
        exam_question__in=all_questions
    )
    if all_questions.count() == completed_questions.count():
        ExamCompletion.objects.update_or_create(
            student=student,
            exam=exam,
            defaults={
                'completed_at': timezone.now()
            }
        )

# 标记完成的年级考试题目
def mark_adminexam_question_as_completed(student, adminexam, adminexam_question):
    AdminExamQuestionCompletion.objects.update_or_create(
        student=student,
        adminexam=adminexam,
        adminexam_question=adminexam_question,
        defaults={
            'completed_at': timezone.now()
        }
    )
    all_questions = adminexam_question.exam.questions.all()
    completed_questions = AdminExamQuestionCompletion.objects.filter(
        student=student,
        adminexam=adminexam,
        adminexam_question__in=all_questions
    )
    if all_questions.count() == completed_questions.count():
        AdminExamCompletion.objects.update_or_create(
            student=student,
            adminexam=adminexam_question.exam,
            defaults={
                'completed_at': timezone.now()
            }
        )

# 运行代码
def run_code(request):
    student = Student.objects.get(pk=request.user.pk)
    user_code = request.POST.get('code', '')
    types = request.POST.get('types', '')
    question_id = request.POST.get('questionId', '')
    client_ip = request.META.get('REMOTE_ADDR')
    if request.method == 'POST':
        # 检查是否在截止时间之前提交代码
        if types == 'exercise':
            question = ExerciseQuestion.objects.get(id=question_id)
            exercise = question.exercise
            if timezone.now() > exercise.deadline:
                return JsonResponse({'status': 'error', 'message': '截止时间已到，不能提交'}, status=400)

        elif types == 'exam':
            question = ExamQuestion.objects.get(id=question_id)
            exam = question.exam
            if timezone.now() > exam.deadline:
                return JsonResponse({'status': 'error', 'message': '截止时间已到，不能提交'}, status=400)

        elif types == 'adminexam':
            question = AdminExamQuestion.objects.get(id=question_id)
            exam = question.exam
            if timezone.now() > exam.deadline:
                return JsonResponse({'status': 'error', 'message': '截止时间已到，不能提交'}, status=400)
        else:
            return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)
        # 保存代码到数据库
        StudentCode.objects.update_or_create(
            student=student,
            question_type=types,
            question_id=question_id,
            defaults={'code': user_code},
        )
        student_code = StudentCode.objects.get(student=student, question_type=types, question_id=question_id)

        # 调用 Django-Q 异步任务
        task_id = async_task('Testingcode_app.task.test_code', student_code.student.userid, student_code.code,
                             student_code.question_type, student_code.question_id, client_ip)

        return JsonResponse({'status': 'success', 'task_id': task_id}, status=200)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)

# 获取代码运行测试结果-mysql
def get_result(request):
    task_id = request.GET.get('task_id')
    if not task_id:
        return JsonResponse({'status': 'error', 'message': '缺少任务ID，测试出现了错误！'}, status=400)

    retries = 10
    delay = 3  # seconds
    # 初始化 task 为 None，用于记录查询结果
    task = None

    # 重试机制，查询任务
    for _ in range(retries):
        try:
            task = Task.objects.get(id=task_id)  # 尝试获取任务
            break  # 如果成功获取任务，则跳出循环
        except Task.DoesNotExist:
            pass  # 如果任务不存在，继续重试
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'查询任务时发生错误: {str(e)}'}, status=500)

        time.sleep(delay)  # 如果查询失败，等待 delay 秒后重试

    # 如果在所有重试后依然没有找到任务
    if not task:
        return JsonResponse({'status': 'error', 'message': '提交任务不存在！请重新提交'}, status=404)

    task_result = task.result
    if not task_result:
        return JsonResponse({'status': 'pending', 'message': '任务正在执行或尚未开始。'}, status=200)

    result_data = task_result
    result_dict = {
        'status': result_data['status'],
        'type': result_data['type'],
        'error': result_data['error'],
        'passed_tests': result_data['passed_tests'],
        'execution_time': result_data['execution_time'],
        'max_memory': result_data['max_memory']
    }

    try:
        if result_data['status'] == 'pass':  # 测试用例全部通过的情况
            if result_data['type'] == 'exercise':
                question = ExerciseQuestion.objects.get(id=result_data['question_id'])
                exercise = question.exercise
                mark_exercise_question_as_completed(result_data['student'], exercise, question)
                Score.objects.update_or_create(
                    student=result_data['student'],
                    exercise=exercise,
                    exercise_question=question,
                    defaults={'score': 10}
                )
            elif result_data['type'] == 'exam':
                question = ExamQuestion.objects.get(id=result_data['question_id'])
                exam = question.exam
                mark_exam_question_as_completed(result_data['student'], exam, question)
                Score.objects.update_or_create(
                    student=result_data['student'],
                    exam=exam,
                    exam_question=question,
                    defaults={'score': 10}
                )
            else:
                question = AdminExamQuestion.objects.get(id=result_data['question_id'])
                adminexam = question.exam
                mark_adminexam_question_as_completed(result_data['student'], adminexam, question)
                Score.objects.update_or_create(
                    student=result_data['student'],
                    adminexam=adminexam,
                    adminexam_question=question,
                    defaults={'score': 10}
                )

            return JsonResponse(result_dict)

        elif result_data['status'] == 'fail':  # 测试用例未全部通过的情况
            passed_tests = result_data['passed_tests']
            total_tests = result_data['testcases'].count()
            score = round((passed_tests / total_tests) * 10, 3)

            if result_data['type'] == 'exercise':
                question = ExerciseQuestion.objects.get(id=result_data['question_id'])
                exercise = question.exercise
                mark_exercise_question_as_completed(result_data['student'], exercise, question)
                Score.objects.update_or_create(
                    student=result_data['student'],
                    exercise=exercise,
                    exercise_question=question,
                    defaults={'score': score}
                )
            elif result_data['type'] == 'exam':
                question = ExamQuestion.objects.get(id=result_data['question_id'])
                exam = question.exam
                mark_exam_question_as_completed(result_data['student'], exam, question)
                Score.objects.update_or_create(
                    student=result_data['student'],
                    exam=exam,
                    exam_question=question,
                    defaults={'score': score}
                )
            else:
                question = AdminExamQuestion.objects.get(id=result_data['question_id'])
                adminexam = question.exam
                mark_adminexam_question_as_completed(result_data['student'], adminexam, question)
                Score.objects.update_or_create(
                    student=result_data['student'],
                    adminexam=adminexam,
                    adminexam_question=question,
                    defaults={'score': score}
                )

                return JsonResponse(result_dict)

        elif result_data['status'] == 'timeout':
            return JsonResponse(result_dict)

        elif result_data['status'] == 'compile error':
            return JsonResponse(result_dict)

        elif result_data['status'] == 'other error':
            return JsonResponse(result_dict)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': '任务执行失败'}, status=400)

