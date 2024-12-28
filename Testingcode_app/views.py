import json
import time

from django.http import JsonResponse
from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from Testingcode_app.models import ExerciseQuestionCompletion, ExerciseCompletion, ExamQuestionCompletion, \
    ExamCompletion, AdminExamQuestionCompletion, AdminExamCompletion, StudentCode, TestResult
from administrator_app.models import AdminExamQuestion
from student_app.models import Student
from teacher_app.models import ExerciseQuestion, ExamQuestion
from Testingcode_app.task import test_code

# Create your views here.
# 标记完成的班级练习题目
def mark_exercise_question_as_completed(student, exercise, exercise_question):
    # 标记该练习题目为完成
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
    # 如果所有的练习题都已经完成，则标记练习为完成
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
    # 标记该考试题目为完成
    ExamQuestionCompletion.objects.update_or_create(
        student=student,
        exam=exam,
        exam_question=exam_question,
        defaults={
            'completed_at': timezone.now()
        }
    )
    # 检查是否所有的考试题都已经完成
    all_questions = exam_question.exam.questions.all()
    completed_questions = ExamQuestionCompletion.objects.filter(
        student=student,
        exam=exam,
        exam_question__in=all_questions
    )
    # 如果所有的考试题都已经完成，则标记考试为完成
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
    # 标记该年级考试题目为完成
    AdminExamQuestionCompletion.objects.update_or_create(
        student=student,
        adminexam=adminexam,
        adminexam_question=adminexam_question,
        defaults={
            'completed_at': timezone.now()
        }
    )
    # 检查是否所有的年级考试题都已经完成
    all_questions = adminexam_question.exam.questions.all()
    completed_questions = AdminExamQuestionCompletion.objects.filter(
        student=student,
        adminexam=adminexam,
        adminexam_question__in=all_questions
    )
    # 如果所有的年级考试题都已经完成，则标记年级考试为完成
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
    # 如果为 POST 请求，则获取用户提交的代码，保存到数据库，并调用异步任务运行代码，并返回任务 ID
    if request.method == 'POST':
        user_code = request.POST.get('code', '')
        types = request.POST.get('types', '')
        question_id = request.POST.get('questionId', '')
        client_ip = request.META.get('REMOTE_ADDR')
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
            return JsonResponse({'status': 'error', 'message': '题目类型无效！测试请求出现了错误！'}, status=400)
        # 未到截止时间，继续执行，保存代码到数据库
        StudentCode.objects.update_or_create(
            student=student,
            question_type=types,
            question_id=question_id,
            defaults={'code': user_code},
        )
        student_code = StudentCode.objects.get(student=student, question_type=types, question_id=question_id)
        # 使用 ThreadPoolExecutor 进行异步任务处理
        with ThreadPoolExecutor() as executor:
            future = executor.submit(test_code, student.userid, student_code.code, student_code.question_type,
                                     student_code.question_id, client_ip)
            task_id = future.result()
        # 返回任务 ID
        return JsonResponse({'status': 'success', 'task_id': task_id}, status=200)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)

# 获取代码运行测试结果-mysql
def get_result(request):
    student = Student.objects.get(pk=request.user.pk)
    # 获取任务 ID, 题目类型和题目 ID
    task_id = request.GET.get('task_id')
    questiontypes = request.GET.get('types')
    question_id = request.GET.get('questionId')
    if not task_id:
        return JsonResponse({'status': 'error', 'message': '缺少任务ID，测试出现了错误！'}, status=400)
    # 重试机制的参数
    retries = 10   # 重试次数
    delay = 3  # seconds
    # 初始化 task_result 为 None，用于记录查询结果
    task_result = None
    # 重试机制，查询任务
    for _ in range(retries):
        try:
            task_result = TestResult.objects.get(id=task_id)  # 尝试获取任务
            if task_result:
                break  # 如果任务存在，跳出循环
        except TestResult.DoesNotExist:
            pass  # 如果任务不存在，继续重试
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'查询任务时发生错误: {str(e)}'}, status=500)
        # 如果查询失败，等待 delay 秒后重试
        time.sleep(delay)
    # 如果在所有重试后依然没有找到任务
    if not task_result:
        return JsonResponse({'status': 'error', 'message': '提交任务不存在！请重新提交'}, status=404)
    # 从TestResult表中获取测试结果
    task_result = TestResult.objects.get(student=student, question_type=questiontypes, question_id=question_id)
    result_dict = {
        'teststatus': task_result.teststatus,
        'testtype': task_result.testtype,
        'error': task_result.error,
        'passed_tests': task_result.passed_tests,
        'testcases': task_result.testcases,
        'execution_time': task_result.execution_time,
        'max_memory': task_result.max_memory
    }
    # 保存测试结果到数据库
    try:
        # 测试用例全部通过的情况
        if result_dict['teststatus'] == 'pass':
            if questiontypes == 'exercise':
                question = ExerciseQuestion.objects.get(id=question_id)
                exercise = question.exercise
                mark_exercise_question_as_completed(student, exercise, question)
            elif questiontypes == 'exam':
                question = ExamQuestion.objects.get(id=question_id)
                exam = question.exam
                mark_exam_question_as_completed(student, exam, question)
            else:
                question = AdminExamQuestion.objects.get(id=question_id)
                adminexam = question.exam
                mark_adminexam_question_as_completed(student, adminexam, question)
            return JsonResponse(result_dict)
        # 测试用例未全部通过的情况
        elif result_dict['teststatus'] == 'fail':
            if questiontypes == 'exercise':
                question = ExerciseQuestion.objects.get(id=question_id)
                exercise = question.exercise
                mark_exercise_question_as_completed(student, exercise, question)
            elif questiontypes == 'exam':
                question = ExamQuestion.objects.get(id=question_id)
                exam = question.exam
                mark_exam_question_as_completed(student, exam, question)
            else:
                question = AdminExamQuestion.objects.get(id=question_id)
                adminexam = question.exam
                mark_adminexam_question_as_completed(student, adminexam, question)
            return JsonResponse(result_dict)
        # 代码运行超时的情况
        elif result_dict['teststatus'] == 'timeout':
            return JsonResponse(result_dict)
        # 编译错误的情况
        elif result_dict['teststatus'] == 'compile error':
            return JsonResponse(result_dict)
        # 其他错误的情况
        elif result_dict['teststatus'] == 'other error':
            return JsonResponse(result_dict)
    # 如果保存测试结果到数据库时出现错误
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    # 如果出现未知错误
    return JsonResponse({'status': 'error', 'message': '出现意外情况，无法获取数据'}, status=400)

