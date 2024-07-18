from __future__ import absolute_import, unicode_literals
import subprocess

import os
from student_app.models import TestResult
from administrator_app.models import AdminExamQuestion, AdminExamQuestionTestCase
from teacher_app.models import (ExerciseQuestion, ExamQuestion,
                                ExerciseQuestionTestCase, ExamQuestionTestCase)


def test_cpp_code(student, code, types, question_id):

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

    # 创建一个新的TestResult实例
    test_result = TestResult.objects.update_or_create(
        student=student,
        question_type=types,
        question_id=question_id,
        testcases=len(testcases),
        defaults={
            'status': None,
            'type': None,
            'error': None,
            'passed_tests': 0,
        },
    )

    # 初始化通过的测试用例的计数器
    passed_tests = 0

    # 逐个运行测试用例
    for i, testcase in enumerate(testcases):
        try:
            result = subprocess.run(
                ['docker', 'run', '--rm', '-v', f"{os.getcwd()}:/app",
                    '-w', '/app', '-m', '512m', '--cpus', '1', 'cpp-runner',
                    'bash', '-c', 'g++ temp.cpp -o temp && echo -n "{}" | ./temp'.format(testcase.input)],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:  # 如果运行成功
                if result.stdout.strip() == testcase.expected_output.strip():
                    passed_tests += 1
                else:
                    passed_tests += 0

            else:  # 如果编译或运行出错
                test_result = TestResult.objects.update_or_create(
                    student=student,
                    question_type=types,
                    question_id=question_id,
                    defaults={
                        'status': 'compile error',
                        'type': '编译错误',
                        'error': result.stderr,
                        'passed_tests': passed_tests,
                    },
                )
                return

        except Exception as e:  # 如果发生其他异常
            test_result = TestResult.objects.update_or_create(
                student=student,
                question_type=types,
                question_id=question_id,
                defaults={
                    'status': 'other error',
                    'type': '其他错误',
                    'error': str(e),
                    'passed_tests': passed_tests,
                },
            )
            return

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


