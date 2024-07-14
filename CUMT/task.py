from __future__ import absolute_import, unicode_literals
import subprocess

from apscheduler.schedulers.background import BackgroundScheduler
from django.core.exceptions import ObjectDoesNotExist

import time
import os


def scan_and_run():
    from student_app.models import StudentCode

    while True:
        try:
            student_code = StudentCode.objects.first()
            if student_code:
                # 运行函数
                test_cpp_code(student_code.student, student_code.code,
                              student_code.question_type, student_code.question_id)
                # 删除已处理的实例
                student_code.delete()
            else:
                break
        except ObjectDoesNotExist:
            break


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scan_and_run, 'interval', seconds=10)
    scheduler.start()


def test_cpp_code(student, code, types, question_id):
    from student_app.models import TestResult, Testcase
    from administrator_app.models import AdminExamQuestion, AdminExamQuestionTestCase
    from teacher_app.models import (ExerciseQuestion, ExamQuestion,
                                    ExerciseQuestionTestCase, ExamQuestionTestCase)
    # 将C++代码写入一个文件
    with open('temp.cpp', 'w') as file:
        file.write(code)

    # 创建一个新的TestResult实例
    test_result = TestResult.objects.update_or_create(
        student=student,
        question_type=types,
        question_id=question_id,
        defaults={
            'status': None,
            'type': None,
            'error': None,
            'passed_tests': None,
        },
    )

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

    # 逐个运行测试用例
    for i, testcase in enumerate(testcases):
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
                    Testcase.objects.update_or_create(
                        testcase=i + 1,
                        defaults={
                            'status': 'success',
                            'type': '答案正确',
                            'error': None,
                            'execution_time': execution_time,
                            'testresult': test_result,
                        },
                    )

                else:
                    Testcase.objects.update_or_create(
                        testcase=i + 1,
                        defaults={
                            'status': 'failure',
                            'type': '答案错误',
                            'error': result.stdout,
                            'execution_time': execution_time,
                            'testresult': test_result,
                        },
                    )

            else:  # 如果编译或运行出错
                test_result = TestResult.objects.update_or_create(
                    student=student,
                    question_type=types,
                    question_id=question_id,
                    defaults={
                        'status': 'compile error',
                        'type': '编译错误',
                        'error': result.stderr,
                        'passed_tests': None,
                    },
                )

        except subprocess.TimeoutExpired:  # 如果运行超时
            Testcase.objects.update_or_create(
                testcase=i + 1,
                defaults={
                    'status': 'failure',
                    'type': '运行超时',
                    'error': '运行超时',
                    'execution_time': execution_time,
                    'testresult': test_result,
                },
            )

        except Exception as e:  # 如果发生其他异常
            test_result = TestResult.objects.update_or_create(
                student=student,
                question_type=types,
                question_id=question_id,
                defaults={
                    'status': 'error',
                    'type': '其他错误',
                    'error': str(e),
                    'passed_tests': None,
                },
            )

    if passed_tests == len(testcases):
        test_result = TestResult.objects.update_or_create(
            student=student,
            question_type=types,
            question_id=question_id,
            defaults={
                'status': 'pass',
                'type': '全部通过',
                'error': None,
                'passed_tests': passed_tests,
            },
        )
    else:
        test_result = TestResult.objects.update_or_create(
            student=student,
            question_type=types,
            question_id=question_id,
            defaults={
                'status': 'fail',
                'type': '部分通过',
                'error': None,
                'passed_tests': passed_tests,
            },
        )


