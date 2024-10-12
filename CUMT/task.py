from __future__ import absolute_import, unicode_literals
import subprocess

import os

from django.utils import timezone

from student_app.models import TestResult
from administrator_app.models import AdminExamQuestion, AdminExamQuestionTestCase
from teacher_app.models import (ExerciseQuestion, ExamQuestion,
                                ExerciseQuestionTestCase, ExamQuestionTestCase)
from submissions_app.models import GradeExamSubmission, ClassExamSubmission


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
        exam = question.exam
    elif types == 'adminexam':
        question = AdminExamQuestion.objects.get(id=question_id)
        testcases = AdminExamQuestionTestCase.objects.filter(question=question)
        exam = question.exam
    else:
        raise ValueError('不存在的题目类型')

    # 创建一个新的TestResult实例
    test_result = TestResult.objects.update_or_create(
        student=student,
        question_type=types,
        question_id=question_id,
        defaults={
            'testcases': len(testcases),
            'status': None,
            'type': None,
            'error': None,
            'passed_tests': 0,
        },
    )

    # 初始化通过的测试用例的计数器
    passed_tests = 0

    # 初始化耗时和内存
    total_time = 0
    max_memory = 0

    # 逐个运行测试用例
    for i, testcase in enumerate(testcases):
        try:
            result = subprocess.run(
                ['docker', 'run', '--rm', '-v', f"{os.getcwd()}:/app",
                    '-w', '/app', '-m', '512m', '--cpus', '1', 'cpp-runner',
                    'bash', '-c', 'time (g++ temp.cpp -o temp && echo -n "{}" | ./temp)'.format(testcase.input)],
                capture_output=True, text=True, timeout=30
            )

            stdout = result.stdout.strip()

            # 解析标准错误以获取时间信息
            stderr = result.stderr.strip()

            # 提取运行时间和内存使用
            for line in stderr.splitlines():
                if 'real' in line:
                    real_time = line.split()[1]  # '0m0.123s'
                    minutes, seconds = map(float, real_time[:-1].split('m'))  # 去掉最后的's'
                    total_time += minutes * 60 + seconds  # 转换为秒
                elif 'Maximum resident set size' in line:
                    max_memory = max(max_memory, int(line.split()[3]))  # 更新最大内存使用

            if result.returncode == 0:  # 如果运行成功
                if stdout == testcase.expected_output.strip():
                    passed_tests += 1
                else:
                    pass

            else:  # 如果编译或运行出错
                test_result, created = TestResult.objects.update_or_create(
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
                break

        except subprocess.TimeoutExpired:
            test_result, created = TestResult.objects.update_or_create(
                student=student,
                question_type=types,
                question_id=question_id,
                defaults={
                    'status': 'timeout',
                    'type': '运行超时',
                    'error': '代码运行超时',
                    'passed_tests': passed_tests,
                },
            )
            break

        except Exception as e:  # 如果发生其他异常
            test_result, created = TestResult.objects.update_or_create(
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
            break

    if passed_tests == len(testcases):
        test_result, created = TestResult.objects.update_or_create(
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
        test_result, created = TestResult.objects.update_or_create(
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

    # 仅记录 'exam' 和 'adminexam' 类型的提交
    if types in ['exam', 'adminexam']:
        submission_time = timezone.now()
        language = 'C++'
        code_length = len(code)

        # 选择对应的提交模型
        if types == 'exam':
            submission_model = ClassExamSubmission
            submission_exam = exam  # Exam对象
            submission_question = question  # ExamQuestion对象
        else:  # 'adminexam'
            submission_model = GradeExamSubmission
            submission_exam = exam  # AdminExam对象
            submission_question = question  # AdminExamQuestion对象

        # 创建提交记录
        submission_record = submission_model.objects.create(
            student_id=student.userid,
            exam=submission_exam,
            question=submission_question,
            result=test_result.status,  # 'pass', 'fail', etc.
            memory=max_memory,  # 这里假设已经获取到内存信息
            time=total_time,  # 这里假设已经获取到时间信息
            language=language,
            code_length=code_length,
            submission_time=submission_time
        )

    # 清理临时文件
    try:
        os.remove('temp.cpp')
        os.remove('temp')  # 如果生成了可执行文件
    except OSError:
        pass




