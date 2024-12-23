# from django_q.tasks import async_task, result
import subprocess
import os
import re

from django.utils import timezone

from Testingcode_app.models import TestResult
from administrator_app.models import AdminExamQuestion, AdminExamQuestionTestCase
from student_app.models import Student
from teacher_app.models import (ExerciseQuestion, ExamQuestion,
                                ExerciseQuestionTestCase, ExamQuestionTestCase)
from submissions_app.models import GradeExamSubmission, ClassExamSubmission

# 解析资源使用信息，计算平均执行时间和平均内存占用
def parse_resource_usage(file_path):
    times = []
    memories = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                match = re.match(r'(\d+) ms (\d+) KB', line.strip())
                if match:
                    time = int(match.group(1))
                    memory = int(match.group(2))
                    times.append(time)
                    memories.append(memory)
        avg_time = sum(times) / len(times) if times else 0
        avg_memory = sum(memories) / len(memories) if memories else 0
        return avg_time, avg_memory
    except Exception as e:
        print(f"An error occurred while parsing resource usage: {e}")
        return 0, 0

# 测试代码
def test_code(student_id, code, types, question_id, ip_address):
    # 临时文件名
    source_file = 'temp.cpp'
    executable_file = 'temp_executable'
    output_file = 'output.txt'
    resource_file = 'resource_usage.txt'

    student = Student.objects.get(userid=student_id)

    # 将C++代码写入一个文件
    with open(source_file, 'w') as file:
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
    test_result, created = TestResult.objects.update_or_create(
        student=student,
        question_type=types,
        question_id=question_id,
        defaults={
            'testcases': len(testcases),
            'status': None,
            'type': None,
            'error': None,
            'passed_tests': 0,
            'execution_time': 0,
            'max_memory': 0
        },
    )

    # 初始化通过的测试用例的计数器
    passed_tests = 0

    # 逐个运行测试用例
    for i, testcase in enumerate(testcases):
        try:
            result = subprocess.run(
                [
                    'docker', 'run', '--rm',
                    '-v', f"{os.getcwd()}:/app",  # 映射工作目录
                    '-w', '/app',  # 容器内工作目录
                    '-m', '512m', '--cpus', '1',  # 资源限制
                    'cpp-runner',  # 使用docker镜像
                    'bash', '-c',
                    # 编译并运行代码，同时测量时间和内存
                    f"(START=$(date +%s%3N); "  # 开始时间
                    f"g++ {source_file} -o {executable_file} && echo -n '{testcase.input}' | ./{executable_file} > {output_file}; "  # 编译和运行
                    f"END=$(date +%s%3N); "  # 结束时间
                    f"echo $((END - START)) ms $(grep VmPeak /proc/self/status | awk '{{print $2}}') KB >> {resource_file})"
                ],
                capture_output=True, text=True, timeout=30
            )
            result.check_returncode()  # 检查命令是否成功执行

            # 检查输出文件以确定测试用例是否通过
            with open(output_file, 'r') as f:
                output = f.read()
                if output.strip() == testcase.expected_output.strip():
                    passed_tests += 1

        except subprocess.CalledProcessError as e:
            test_result, created = TestResult.objects.update_or_create(
                student=student,
                question_type=types,
                question_id=question_id,
                defaults={
                    'status': 'compile error',
                    'type': '编译错误',
                    'error': e.stderr,
                    'passed_tests': passed_tests,
                    'execution_time': 0,
                    'max_memory': 0,
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
                    'execution_time': 0,  # 添加运行时间
                    'max_memory': 0,  # 添加最大内存使用
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
                    'execution_time': 0,  # 添加运行时间
                    'max_memory': 0,  # 添加最大内存使用
                },
            )
            break

    # 计算平均运行时间和内存使用
    avg_time, avg_memory = parse_resource_usage(resource_file)

    # 更新最终的测试结果
    final_status = 'pass' if passed_tests == len(testcases) else 'fail'
    final_type = '全部通过' if final_status == 'pass' else '部分通过'

    test_result, created = TestResult.objects.update_or_create(
        student=student,
        question_type=types,
        question_id=question_id,
        defaults={
            'status': final_status,
            'type': final_type,
            'error': None,
            'passed_tests': passed_tests,
            'execution_time': avg_time,
            'max_memory': avg_memory,
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
            memory=avg_memory,  # 这里假设已经获取到内存信息
            time=avg_time,  # 这里假设已经获取到时间信息
            language=language,
            code_length=code_length,
            ip_address=ip_address,
            submission_time=submission_time
        )

    # 清理临时文件
    for file in [source_file, executable_file, output_file, resource_file]:
        try:
            os.remove(file)
        except OSError:
            pass

    return {
        'student': student,
        'question_id': question_id,
        'status': test_result.status,
        'type': test_result.type,
        'error': test_result.error,
        'passed_tests': test_result.passed_tests,
        'testcases': testcases,
        'execution_time': test_result.execution_time,
        'max_memory': test_result.max_memory,
        'test_result_id': test_result.id,
    }
