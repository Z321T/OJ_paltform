import os
import re
import subprocess
import timeit
import uuid

import psutil
from django.utils import timezone

from Testingcode_app.models import Scores, TestResult
from administrator_app.models import AdminExamQuestion, AdminExamQuestionTestCase
from student_app.models import Student
from submissions_app.models import ClassExamSubmission, GradeExamSubmission
from teacher_app.models import ExerciseQuestion, ExerciseQuestionTestCase, ExamQuestion, ExamQuestionTestCase


# 测试代码
def test_code(student_id, code, types, question_id, ip_address):
    # 获取学生对象
    student = Student.objects.get(userid=student_id)
    # 获取当前工作目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cpp_file_path = os.path.join(current_dir, "temp_files")
    os.makedirs(cpp_file_path, exist_ok=True)
    # 临时文件名
    source_file = os.path.join(cpp_file_path, f'temp_{uuid.uuid4().hex}.cpp')
    executable_file = os.path.join(cpp_file_path, f'temp_executable_{uuid.uuid4().hex}')

    # 将 C++ 代码写入文件
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
    # 初始化通过的测试用例的计数器，最终状态和类型， 错误信息
    passed_tests = 0
    final_status = 'fail'
    final_type = '未通过'
    error_message = None
    total_execution_time_ms = 0
    total_memory_usage_kb = 0
    # 逐个运行测试用例
    for testcase in testcases:
        try:
            # 编译 C++ 代码
            compile_command = f"g++ {source_file} -o {executable_file}"
            subprocess.run(compile_command, shell=True, check=True, stderr=subprocess.PIPE)
            # 运行编译后的可执行文件并记录时间和内存使用
            start_time = timeit.default_timer()
            process = subprocess.Popen(
                f'echo {testcase.input} | {executable_file}',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # 在进程结束前获取内存信息
            try:
                memory_info = psutil.Process(process.pid).memory_info()
                memory_usage_kb = memory_info.rss / 1024
                total_memory_usage_kb += memory_usage_kb
            except psutil.NoSuchProcess:
                # 如果进程已结束，忽略内存统计
                memory_usage_kb = 0
            # 等待进程结束并捕获输出
            stdout, stderr = process.communicate()
            end_time = timeit.default_timer()
            # 计算执行时间
            execution_time_ms = (end_time - start_time) * 1000
            total_execution_time_ms += execution_time_ms
            # 检查输出以确定测试用例是否通过
            output = stdout.decode().strip()
            if output == testcase.expected_output.strip():
                passed_tests += 1



        # 捕获编译错误
        except subprocess.CalledProcessError as e:
            final_status = 'compile error'
            final_type = '编译错误'
            error_message = e.stderr.decode('utf-8')[0:255]
            break
        # 捕获运行超时
        except subprocess.TimeoutExpired:
            final_status = 'timeout'
            final_type = '运行超时'
            error_message = '代码运行超时'
            break
        # 捕获其他异常
        except Exception as e:
            final_status = 'other error'
            final_type = '其他错误'
            error_message = str(e)[:255]
            break
    # 计算平均运行时间和内存使用
    avg_execution_time_ms = total_execution_time_ms / len(testcases) if testcases else 0
    avg_memory_usage_kb = total_memory_usage_kb / len(testcases) if testcases else 0

    # 更新最终的测试结果
    if final_status == 'fail' and passed_tests == len(testcases):
        final_status = 'pass'
        final_type = '全部通过'
    # 记录得分
    if final_status == 'pass':
        score = question.score
    else:
        score = (passed_tests / len(testcases)) * question.score
    # 更新或创建得分记录
    Scores.objects.update_or_create(
        student=student,
        question_type=types,
        type_id=question.exercise.id if types == 'exercise' else question.exam.id,
        question_id=question.id,
        defaults={'score': score}
    )
    # 创建或更新测试结果
    test_result, created = TestResult.objects.update_or_create(
        student=student,
        question_type=types,
        question_id=question_id,
        defaults={
            'teststatus': final_status,
            'testtype': final_type,
            'error': error_message,
            'passed_tests': passed_tests,
            'testcases': len(testcases),
            'execution_time': avg_execution_time_ms,
            'max_memory': avg_memory_usage_kb,
        },
    )
    # 仅记录 'exam' 和 'adminexam' 类型的提交
    if types in ['exam', 'adminexam']:
        submission_time = timezone.now()
        language = 'C++'    # 目前代码测试仅支持C++
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
            result=final_status,  # 'pass', 'fail', 'timeout', 'compile error', 'other error'
            memory=avg_memory_usage_kb,  # 获取到内存信息
            time=avg_execution_time_ms,  # 获取到时间信息
            language=language,
            code_length=code_length,
            ip_address=ip_address,
            submission_time=submission_time
        )
    # 清理临时文件
    for file in [source_file,executable_file]:
        try:
            if os.path.exists(file):
                os.remove(file)
        except OSError:
            pass

    return test_result.id
