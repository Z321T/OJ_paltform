import time
from threading import Lock

from django.core.exceptions import ObjectDoesNotExist
from django.forms import model_to_dict
from django.http import JsonResponse
from django.utils import timezone

from Testingcode_app.models import ExerciseQuestionCompletion, ExerciseCompletion, ExamQuestionCompletion, \
    ExamCompletion, AdminExamQuestionCompletion, AdminExamCompletion, StudentCode, TestResult, Score
from Testingcode_app.task import test_cpp_code
from administrator_app.models import AdminExamQuestion
from student_app.models import Student
from teacher_app.models import ExerciseQuestion, ExamQuestion

# 创建一个全局锁实例
lock = Lock()


# Create your views here.
# 标记完成的题目
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


# 运行C++代码
def run_cpp_code(request):
    student = Student.objects.get(pk=request.user.pk)
    user_code = request.POST.get('code', '')
    types = request.POST.get('types', '')
    question_id = request.POST.get('questionId', '')
    client_ip = request.META.get('REMOTE_ADDR')
    if request.method == 'POST':
        # 尝试获取锁
        if not lock.acquire(blocking=False):
            return JsonResponse({'status': 'error', 'message': '当前测评人数较多，请稍后提交。'}, status=400)

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

        #  调用运行代码的测试函数
        test_cpp_code(student_code.student, student_code.code, student_code.question_type, student_code.question_id, client_ip)
        # 释放锁
        lock.release()

        # 等待测试结果
        result = None
        for _ in range(50):  # 最多等待 50 次，每次间隔 5 秒
            try:
                result = TestResult.objects.get(student=student, question_type=types, question_id=question_id)
                if result.status is not None:
                    # 将对象转换为字典
                    # 测试结果已生成
                    result_dict = model_to_dict(result)
                    break
            except ObjectDoesNotExist:
                time.sleep(5)
        if result is None:
            return JsonResponse({'status': 'error', 'message': '测试出现错误，请重新提交'}, status=400)

        # 获取任务结果
        try:
            if result.status == 'pass':
                # 测试用例全部通过的情况
                if types == 'exercise':
                    question = ExerciseQuestion.objects.get(id=question_id)
                    exercise = question.exercise
                    mark_exercise_question_as_completed(student, exercise, question)
                    Score.objects.update_or_create(
                        student=student,
                        exercise=exercise,
                        exercise_question=question,
                        defaults={'score': 10}
                    )
                elif types == 'exam':
                    question = ExamQuestion.objects.get(id=question_id)
                    exam = question.exam
                    mark_exam_question_as_completed(student, exam, question)
                    Score.objects.update_or_create(
                        student=student,
                        exam=exam,
                        exam_question=question,
                        defaults={'score': 10}
                    )
                else:
                    question = AdminExamQuestion.objects.get(id=question_id)
                    adminexam = question.exam
                    mark_adminexam_question_as_completed(student, adminexam, question)
                    Score.objects.update_or_create(
                        student=student,
                        adminexam=adminexam,
                        adminexam_question=question,
                        defaults={'score': 10}
                    )

                # 添加运行时间和内存信息
                result_dict['execution_time'] = result.execution_time
                result_dict['max_memory'] = result.max_memory

                result.delete()
                return JsonResponse(result_dict)

            elif result.status == 'fail':
                # 测试用例未全部通过的情况
                passed_tests = result.passed_tests
                total_tests = result.testcases
                score = round((passed_tests / total_tests) * 10, 3)

                if types == 'exercise':
                    question = ExerciseQuestion.objects.get(id=question_id)
                    exercise = question.exercise
                    mark_exercise_question_as_completed(student, exercise, question)
                    Score.objects.update_or_create(
                        student=student,
                        exercise=exercise,
                        exercise_question=question,
                        defaults={'score': score}
                    )
                elif types == 'exam':
                    question = ExamQuestion.objects.get(id=question_id)
                    exam = question.exam
                    mark_exam_question_as_completed(student, exam, question)
                    Score.objects.update_or_create(
                        student=student,
                        exam=exam,
                        exam_question=question,
                        defaults={'score': score}
                    )
                else:
                    question = AdminExamQuestion.objects.get(id=question_id)
                    adminexam = question.exam
                    mark_adminexam_question_as_completed(student, adminexam, question)
                    Score.objects.update_or_create(
                        student=student,
                        adminexam=adminexam,
                        adminexam_question=question,
                        defaults={'score': score}
                    )

                # 添加运行时间和内存信息
                result_dict['execution_time'] = result.execution_time
                result_dict['max_memory'] = result.max_memory
                print(result_dict)
                result.delete()
                return JsonResponse(result_dict)

            elif result.status == 'timeout':
                # 添加运行时间和内存信息
                result_dict['execution_time'] = result.execution_time
                result_dict['max_memory'] = result.max_memory
                result.delete()
                # 出现运行超时的情况
                return JsonResponse(result_dict)

            elif result.status == 'compile error':
                # 添加运行时间和内存信息
                result_dict['execution_time'] = result.execution_time
                result_dict['max_memory'] = result.max_memory
                result.delete()
                # 出现编译错误的情况
                return JsonResponse(result_dict)

            elif result.status == 'other error':
                # 添加运行时间和内存信息
                result_dict['execution_time'] = result.execution_time
                result_dict['max_memory'] = result.max_memory
                result.delete()
                # 出现其他错误的情况
                return JsonResponse(result_dict)

        except Exception as e:
            # 添加运行时间和内存信息
            result_dict['execution_time'] = result.execution_time
            result_dict['max_memory'] = result.max_memory
            result.delete()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)