from __future__ import absolute_import, unicode_literals
from celery import shared_task
import subprocess
from django.utils import timezone
from administrator_app.models import AdminExam, AdminExamQuestion, AdminExamQuestionTestCase
from student_app.models import (Student, Score, ExerciseCompletion, ExerciseQuestionCompletion,
                                ExamCompletion, ExamQuestionCompletion,
                                AdminExamCompletion, AdminExamQuestionCompletion)
from teacher_app.models import (Exercise, Exam, ExerciseQuestion, ExamQuestion,
                                ExerciseQuestionTestCase, ExamQuestionTestCase)
import time
import os


@shared_task
def test_cpp_code(code, types, question_id, student):
    # 将C++代码写入一个文件
    with open('temp.cpp', 'w') as file:
        file.write(code)

    # 获取与题目相关的测试用例
    if types == 'exercise':
        question = ExerciseQuestion.objects.get(id=question_id)
        testcases = ExerciseQuestionTestCase.objects.filter(question=question)
    elif types == 'exam':
        question = ExamQuestion.objects.get(id=question_id)
        testcases = ExamQuestionTestCase.objects.filter(question=question)
    else:
        question = AdminExamQuestion.objects.get(id=question_id)
        testcases = AdminExamQuestionTestCase.objects.filter(question=question)

    # 初始化通过的测试用例的计数器
    passed_tests = 0
    # 创建一个列表来收集失败的测试用例的信息
    failed_tests = []

    # 逐个运行测试用例
    for testcase in testcases:
        try:
            start_time = time.time()  # 记录开始时间
            result = subprocess.run(
                ['docker', 'run', '--rm', '-v', f"{os.getcwd()}:/app",
                    '-w', '/app', '-m', '512m', '--cpus', '1', 'cpp-runner',
                    'bash', '-c', 'g++ temp.cpp -o temp && echo -n "{}" | ./temp'.format(testcase.input)],
                capture_output=True, text=True, timeout=30
            )
            execution_time = time.time() - start_time  # 计算执行时间

            if result.returncode == 0:  # 如果运行成功
                if result.stdout.strip() == testcase.expected_output.strip():
                    passed_tests += 1
                else:
                    failed_tests.append({
                        'output': result.stdout,
                        'error': 'Wrong answer',
                        'time': execution_time,
                        'type': '答案错误'
                    })

            else:  # 如果编译或运行出错,直接返回错误信息
                return {
                    'status': 'compile error',
                    'error': result.stderr,
                    'time': execution_time,
                    'type': '编译错误'
                }

        except subprocess.TimeoutExpired:  # 如果运行超时
            failed_tests.append({
                'error': 'Execution timed out',
                'type': '运行超时'
            })

        except Exception as e:  # 如果发生其他异常
            failed_tests.append({
                'error': str(e),
                'type': '其他错误'
            })

    # 如果所有测试用例都通过，返回成功状态和通过的测试用例的数量
    if not failed_tests:
        return {
            'status': 'success',
            'message': '题目作答正确',
            'time': execution_time,
            'passed_tests': passed_tests
        }
    else:
        # 如果有测试用例没通过，返回失败的测试用例的信息
        return {
            'status': 'failure',
            'failed_tests': failed_tests,
            'passed_tests': passed_tests
        }

