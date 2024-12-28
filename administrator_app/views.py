import os
import tempfile
import docx
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

from django.contrib.auth.hashers import make_password, check_password
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import DatabaseError
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from BERT_app.views import analyze_programming_report, analyze_programming_code
from administrator_app.models import (Administrator, AdminNotification, ProgrammingExercise,
                                      AdminExam, AdminExamQuestion, AdminExamQuestionTestCase)
from teacher_app.models import Teacher, Class
from student_app.models import Student
from BERT_app.models import ReportStandardScore, ProgrammingCodeFeature, ProgrammingReportFeature
from login.views import login_required
from submissions_app.models import GradeExamSubmission
from Testingcode_app.models import Scores


# 课程负责人主页-程序设计
@login_required
def home_administrator(request):
    try:
        administrator = Administrator.objects.get(pk=request.user.pk)
        user_id = administrator.userid
        # 尝试获取编程练习信息，并按日期倒序排列
        programings = ProgrammingExercise.objects.filter(posted_by=administrator).order_by('-date_posted')
        # 前端模版渲染内容
        context = {
            'active_page': 'home',
            'user_id': user_id,
            'coursework': programings,
        }
        # 正常渲染页面
        return render(request, 'home_administrator.html', context)
    # 捕获会话获取错误
    except KeyError:
        return render(request, 'error.html', {'message': "会话中未找到用户ID"}, status=400)
    # 捕获数据库相关错误
    except DatabaseError as db_err:
        return render(request, 'error.html', {'message': "无法连接到数据库，请稍后重试"}, status=500)
    # 捕获其他未预见的错误
    except Exception as e:
        return render(request, 'error.html', {'message': f"发生未知错误: {e}"}, status=500)

# 课程负责人主页-年级考试
@login_required
def home_administrator_exam(request):
    try:
        administrator = Administrator.objects.get(pk=request.user.pk)
        user_id = administrator.userid
        # 尝试删除标题为"默认标题"的记录
        AdminExam.objects.filter(title="默认标题").delete()
        # 获取所有考试信息，并按开始时间倒序排列
        exams = AdminExam.objects.filter(teacher=administrator).order_by('-starttime')
        # 构建上下文
        context = {
            'active_page': 'home',
            'user_id': user_id,
            'coursework': exams,
        }
        # 正常渲染页面
        return render(request, 'home_administrator_exam.html', context)
        # 捕获会话获取错误
    except KeyError:
        return render(request, 'error.html', {'message': "会话中未找到用户ID"}, status=400)
        # 捕获数据库相关错误
    except DatabaseError as db_err:
        return render(request, 'error.html', {'message': "数据库操作失败，请稍后重试"}, status=500)
        # 捕获其他未预见的错误
    except Exception as e:
        return render(request, 'error.html', {'message': f"发生未知错误: {e}"}, status=500)

# 课程负责人主页-程序设计题详情
@login_required
def programmingexercise_details_data(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    # 尝试获取题目ID
    try:
        if request.method == 'POST':
            question_id = request.POST.get('id')
            # 尝试获取指定的编程练习题
            try:
                question = ProgrammingExercise.objects.get(id=question_id)
                # 获取当前题目所有学生
                teachers = administrator.teachers.all()
                classes = Class.objects.filter(teacher__in=teachers).distinct()
                students = Student.objects.filter(class_assigned__in=classes).distinct()
                total_students = students.count()
                # 获取当前题目所有分数对象，来等效于提交记录
                total_submissions = ReportStandardScore.objects.filter(programming_question=question).count()
                ratio = total_submissions / total_students if total_students else 0
                ratio_data = [{
                    'completion_rate': ratio,
                }]
                context = {
                    'ratio_data': ratio_data,
                }
                return JsonResponse({'data': context}, status=200)
            except ProgrammingExercise.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': '未找到对应的练习题'}, status=404)
        else:
            return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)
    # 捕获数据库相关错误
    except DatabaseError as db_err:
        return JsonResponse({'status': 'error', 'message': '数据库操作失败，请稍后重试'}, status=500)
    # 捕获其他未预见的错误
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'发生未知错误: {e}'}, status=500)

# 课程负责人主页-年级考试题详情
@login_required
def exam_details_data(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    # 尝试获取题目ID
    try:
        if request.method == 'POST':
            exam_id = request.POST.get('id')
            # 尝试获取指定的考试
            try:
                exam = AdminExam.objects.get(id=exam_id)
                questions = exam.questions.all()
                question_avg_scores = []
                # 遍历所有题目，计算平均分，若学生总数为0，则平均分为0，否则计算平均分
                for question in questions:
                    # 获取当前题目所有分数对象
                    scores = Scores.objects.filter(question_type='adminexam', type_id=exam.id, question_id=question.id)
                    total_score = sum(score.score for score in scores)
                    # 获取当前题目所有学生
                    teachers = administrator.teachers.all()
                    classes = Class.objects.filter(teacher__in=teachers).distinct()
                    students = Student.objects.filter(class_assigned__in=classes).distinct()
                    total_students = students.count()
                    # 计算平均分，若学生总数为0，则平均分为0
                    avg_score = (total_score / total_students) if total_students else 0
                    # 将题目标题和平均分添加到列表中
                    question_avg_scores.append({
                        'question_title': question.title,
                        'average_score': avg_score
                    })
                return JsonResponse({'data': question_avg_scores}, status=200)
            except AdminExam.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': '未找到对应的考试'}, status=404)
        else:
            return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)
    # 捕获数据库相关错误
    except DatabaseError as db_err:
        return JsonResponse({'status': 'error', 'message': '数据库操作失败，请稍后重试'}, status=500)
    # 捕获其他未预见的错误
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'发生未知错误: {e}'}, status=500)

# 年级考试实况
@login_required
def admintest_check_process(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 初始化默认值
    exam_type = None
    exam_id = None
    selected_exam = None
    submissions = []
    # 尝试获取考试类型和考试ID
    if request.method == 'GET':
        exam_type = request.GET.get('exam_type')
        exam_id = request.GET.get('exam_id')
        # 若考试类型和考试ID均存在，则获取对应的考试信息和提交记录
        if exam_type and exam_id:
            selected_exam = AdminExam.objects.filter(id=exam_id).first()
            submissions = GradeExamSubmission.objects.filter(exam=selected_exam).order_by('-submission_time')
        # 渲染页面
        context = {
            'active_page': 'testcheck',
            'user_id': user_id,
            'selected_exam': selected_exam,
            'submissions': submissions,
            'exam_type': exam_type,
            'exam_id': exam_id,
        }
        return render(request, 'admintest_check_process.html', context)

# 年级考试实况-获取考试项目
@login_required
def get_adminexam_names(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    # 尝试获取考试类型
    exam_type = request.GET.get('exam_type')
    # 尝试获取
    try:
        if exam_type == 'adminexam':
            exams = AdminExam.objects.filter(teacher=administrator)
        else:
            exams = []
        # 构建考试名称列表
        exam_names = [{'id': exam.id, 'name': exam.title} for exam in exams]
        return JsonResponse({'exam_names': exam_names})
    except Administrator.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '未找到管理员信息，请确认用户是否为管理员。'}, status=404)
    except DatabaseError as db_err:
        return JsonResponse({'status': 'error', 'message': '数据库操作失败，请稍后重试。'}, status=500)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'发生未知错误: {e}'}, status=500)

# GUI程序设计题库
@login_required
def repository_administrator(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 获取所有编程练习题，并按日期倒序排列
    programming_exercises = ProgrammingExercise.objects.filter(posted_by=administrator).order_by('-date_posted')
    # 前端模版渲染内容
    context = {
        'active_page': 'guirepository',
        'user_id': user_id,
        'programming_exercises': programming_exercises,
    }
    return render(request, 'repository_administrator.html', context)

# 程序设计题库：添加程序设计题
@login_required
def programmingexercise_create(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 尝试获取POST请求，创建新的编程练习题，若标题、描述、截止时间和发布者均存在，则创建新的编程练习题，并重定向到题库页面，否则渲染创建页面
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('content')
        deadline = request.POST.get('deadline')
        posted_by = administrator.userid
        # 确保标题、描述、截止时间和发布者均存在
        if title and description and deadline and posted_by:
            # 确保 deadline 包含时区信息
            deadline = datetime.fromisoformat(deadline)
            deadline = timezone.make_aware(deadline, timezone.get_current_timezone())
            ProgrammingExercise.objects.create(
                title=title,
                description=description,
                deadline=deadline,
                posted_by=Administrator.objects.get(userid=posted_by)
            )
            return redirect('administrator_app:repository_administrator')
    # 渲染创建页面
    conetxt = {
        'active_page': 'guirepository',
        'user_id': user_id,
    }
    return render(request, 'programmingexercise_create.html', conetxt)

# 程序设计题库：删除程序设计题
@login_required
def programmingexercise_delete(request):
    # 尝试获取POST请求，删除指定的编程练习题，若题目ID存在，则删除对应的编程练习题，否则返回错误信息
    if request.method == 'POST':
        exercise_id = request.POST.get('exercise_id')
        if exercise_id:
            exercise_to_delete = ProgrammingExercise.objects.filter(id=exercise_id)
            exercise_to_delete.delete()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': '练习未找到'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)

# 题库查重管理
@login_required
def problems_administrator(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 获取所有编程练习题，并按日期倒序排列
    programming_exercises = ProgrammingExercise.objects.filter(posted_by=administrator).order_by('-date_posted')
    # 前端模版渲染内容
    context = {
        'active_page': 'problemsmanage',
        'user_id': user_id,
        'programming_exercises': programming_exercises,
    }
    return render(request, 'problems_administrator.html', context)

# 题库查重管理-导入数据
@login_required
def report_administrator(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 尝试获取题目ID
    programmingexercise_id = request.GET.get('exerciseId')
    # 尝试获取POST请求，读取上传的Word文档和TXT文件，分析报告特征和代码特征，若成功则返回成功信息，否则返回错误信息
    if request.method == 'POST':
        student = None
        word_file = request.FILES['wordFile']
        if word_file:
            # 读取文件内容并使用BytesIO创建一个类似文件的对象
            word_file_bytes = BytesIO(word_file.read())
            # 使用BytesIO对象创建docx文档对象
            document = docx.Document(word_file_bytes)
            full_text = []
            for paragraph in document.paragraphs:
                full_text.append(paragraph.text)
            # 获得纯文本代码，去除了图片
            report = '\n'.join(full_text)
            # 分析报告特征
            analyze_programming_report(student, report, programmingexercise_id)
        # 读取TXT文件内容
        code_file = request.FILES.get('txtFile')
        if code_file:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            temp_file.write(code_file.read())
            temp_file.close()
            # 分析代码特征
            code = open(temp_file.name, encoding='utf-8').read()
            analyze_programming_code(student, code, programmingexercise_id)
            os.unlink(temp_file.name)
        return JsonResponse({'status': 'success', 'message': '提交成功'}, status=200)
    # 渲染页面
    context = {
        'active_page': 'problemsmanage',
        'user_id': user_id,
    }
    return render(request, 'report_administrator.html', context)

# 题库查重管理-删除数据
@login_required
def reportdata_delete(request):
    # 尝试获取POST请求，删除指定的编程练习题的所有学生为null的报告特征和代码特征，若题目ID存在，则删除对应的报告特征和代码特征，否则返回错误信息
    programmingexercise_id = request.POST.get('exerciseId')
    if programmingexercise_id:
        # 查询对应题目所有student为null的ProgrammingCodeFeature实例
        programmingexercise = ProgrammingExercise.objects.get(id=programmingexercise_id)
        codefeatures_to_delete = ProgrammingCodeFeature.objects.filter(
            programming_question=programmingexercise,
            student__isnull=True
        )
        # 执行删除操作
        codefeatures_to_delete.delete()
        # 查询对应题目所有student为null的ProgrammingReportFeature实例
        reportfeatures_to_delete = ProgrammingReportFeature.objects.filter(
            programming_question=programmingexercise,
            student__isnull=True
        )
        reportfeatures_to_delete.delete()
        return JsonResponse({'status': 'success', 'message': '数据删除成功'}, status=200)
    else:
        return JsonResponse({'status': 'error', 'message': '未找到对应的练习题'}, status=404)

# 年级考试
@login_required
def exam_administrator(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 尝试删除标题为"默认标题"的记录, 获取所有考试信息，并按开始时间倒序排列
    AdminExam.objects.filter(title="默认标题").delete()
    exams = AdminExam.objects.filter(teacher=administrator).order_by('-starttime')
    # 前端模版渲染内容
    context = {
        'active_page': 'adminexam',
        'user_id': user_id,
        'exams': exams,
    }
    return render(request, 'exam_administrator.html', context)

# 考试-考试列表
@login_required
def admin_examlist_default(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 创建默认考试
    exam = AdminExam.objects.create(
        title="默认标题",
        content="默认内容",
        starttime=timezone.now(),
        deadline=timezone.now() + timedelta(days=7),
        teacher=administrator
    )
    # 前端模版渲染内容
    context = {
        'active_page': 'adminexam',
        'user_id': user_id,
        'exam': exam,
    }
    return render(request, 'admin_examlist.html', context)

@login_required
def admin_examlist(request, exam_id):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 获取指定的考试
    exam = get_object_or_404(AdminExam, id=exam_id)
    if request.method == 'POST':
        exam.title = request.POST.get('title')
        exam.content = request.POST.get('content')
        exam.starttime = timezone.make_aware(datetime.fromisoformat(request.POST.get('starttime')),
                                             timezone.get_current_timezone())
        exam.deadline = timezone.make_aware(datetime.fromisoformat(request.POST.get('deadline')),
                                            timezone.get_current_timezone())
        # 获取当前课程负责人的所有教师的关联班级
        teachers = administrator.teachers.all()
        recipient_class = Class.objects.filter(teacher__in=teachers).distinct()
        if recipient_class:
            exam.save()
            exam.classes.set(recipient_class)
            return redirect('administrator_app:exam_administrator')
    # 前端模版渲染内容
    context = {
        'active_page': 'adminexam',
        'user_id': user_id,
        'exam': exam,
    }
    return render(request, 'admin_examlist.html', context)

# 考试-考试列表-创建考试题
@login_required
def create_adminexam(request, exam_id):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 获取指定的考试
    exam = get_object_or_404(AdminExam, id=exam_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        memory_limit = request.POST.get('memory_limit')
        time_limit = request.POST.get('time_limit')
        question_id = request.POST.get('question_id')
        score = request.POST.get('score') or 10
        # 处理上传的 Excel 文件
        if 'testcase_file' in request.FILES:
            testcase_file = request.FILES['testcase_file']
            if isinstance(testcase_file, InMemoryUploadedFile):
                try:
                    df = pd.read_excel(testcase_file)
                    # 检查DataFrame是否为空
                    if df.empty:
                        raise ValueError('Excel文件为空，请上传有效的文件。')
                    # 检查第一行的列名
                    expected_columns = ['input', 'output']
                    if not all(col in df.columns for col in expected_columns):
                        raise ValueError('Excel文件格式不正确，必须包含“input”和“output”列。')
                    if question_id:
                        question = AdminExamQuestion.objects.get(id=question_id)
                        question.title = title
                        question.content = content
                        question.memory_limit = memory_limit
                        question.time_limit = time_limit
                        question.score = score
                        question.save()
                        # 删除原有的测试用例
                        AdminExamQuestionTestCase.objects.filter(question=question).delete()
                    else:
                        question = AdminExamQuestion.objects.create(
                            title=title,
                            content=content,
                            memory_limit=memory_limit,
                            time_limit=time_limit,
                            exam=exam,
                            score=score
                        )
                    # 初始化测试用例列表
                    test_cases = [
                        AdminExamQuestionTestCase(
                            question=question,
                            input=row['input'],
                            expected_output=row['output']
                        ) for index, row in df.iterrows()  # 跳过标题行
                    ]
                    AdminExamQuestionTestCase.objects.bulk_create(test_cases)
                # 捕获空数据错误
                except pd.errors.EmptyDataError:
                    return JsonResponse({'status': 'error', 'message': '上传的文件为空，请提供测试用例文件。'}, status=400)
                except pd.errors.ParserError:
                    return JsonResponse({'status': 'error', 'message': '文件解析错误，请检查文件格式。'}, status=400)
                except ValueError as ve:
                    return JsonResponse({'status': 'error', 'message': str(ve)}, status=400)
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': f'未知错误: {str(e)}'}, status=400)
        return redirect('administrator_app:admin_examlist', exam_id=exam.id)
    # 前端模版渲染内容
    context = {
        'active_page': 'adminexam',
        'user_id': user_id,
        'exam': exam,
    }
    return render(request, 'create_adminexam.html', context)

# 考试-考试列表-修改考试题
@login_required
def adminexam_edit(request, exam_id):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 获取指定的考试
    if request.method == 'GET':
        exam = AdminExam.objects.get(id=exam_id)
        context = {
            'active_page': 'adminexam',
            'user_id': user_id,
            'exam': exam,
        }
        return render(request, 'adminexam_edit.html', context)

# 考试-考试列表-删除考试
@login_required
def adminexam_delete(request):
    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        if exam_id:
            exam_to_delete = AdminExam.objects.filter(id=exam_id).first()
            if exam_to_delete:
                exam_to_delete.questions.all().delete()
                exam_to_delete.classes.clear()
                exam_to_delete.delete()
                return JsonResponse({'status': 'success'}, status=200)
        return JsonResponse({'status': 'error', 'message': '考试未找到'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)

# 考试-考试列表-获取考试题测试用例
@login_required
def get_adminexam_cases(request, question_id):
    # 确保该题目存在
    try:
        question = AdminExamQuestion.objects.get(id=question_id)
        # 获取该题目下的所有测试用例
        test_cases = question.adminexam_testcases.values('input', 'expected_output')
        # 检查请求是否包含下载请求
        if request.GET.get('download') == 'true':
            # 检查测试用例是否为空
            if not test_cases:
                return JsonResponse({"status": "error", "message": "没有可用的测试用例数据"}, status=400)
            # 创建 DataFrame 并导出为 Excel 文件
            df = pd.DataFrame(list(test_cases), columns=['input', 'expected_output'])
            df.columns = ['input', 'output']  # 重命名列为 'input' 和 'output'
            # 创建 HttpResponse 对象并设置响应头
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="adminexam_{str(question_id)}_cases.xlsx"'
            df.to_excel(response, index=False, sheet_name='Test Cases', engine='openpyxl')
            return response
        return JsonResponse({"status": "success", "test_cases": list(test_cases)}, safe=False)
    except AdminExamQuestion.DoesNotExist:
        return JsonResponse({"status": "error", "message": "题目不存在"}, status=404)

# 考试-考试列表-修改考试题
@login_required
def adminexamquestion_edit(request, question_id):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 获取指定的考试题
    question = AdminExamQuestion.objects.get(id=question_id)
    exam = question.exam
    # 处理POST请求，更新考试题信息
    if request.method == 'GET':
        question = AdminExamQuestion.objects.get(id=question_id)
        context = {
            'active_page': 'adminexam',
            'user_id': user_id,
            'question': question,
            'exam': exam,
        }
        return render(request, 'adminexamquestion_edit.html', context)

# 考试-考试列表-删除考试题
@login_required
def adminexamquestion_delete(request):
    if request.method == 'POST':
        adminexam_id = request.POST.get('exam_id')
        question_id = request.POST.get('question_id')
        if AdminExam.objects.filter(id=adminexam_id).exists():
            if question_id:
                question_to_delete = AdminExamQuestion.objects.filter(id=question_id).first()
                if question_to_delete:
                    question_to_delete.delete()
                    return JsonResponse({'status': 'success'}, status=200)
        return JsonResponse({'status': 'error', 'message': '考试题未找到'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)

# 通知界面
@login_required
def notice_administrator(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 获取所有通知信息，并按发布日期倒序排列
    adminnotifications = AdminNotification.objects.filter(administrator=administrator).order_by('-date_posted')
    # 前端模版渲染内容
    context = {
        'active_page': 'notice',
        'user_id': user_id,
        'adminnotifications': adminnotifications,
    }
    return render(request, 'notice_administrator.html', context)

# 通知界面：发布通知
@login_required
def create_notice(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 处理POST请求，创建新的通知
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('message')
        if title and content:
            adminnotification = AdminNotification.objects.create(
                administrator=administrator,
                title=title,
                content=content,
            )
            adminnotification.save()
            return redirect('administrator_app:notice_administrator')
    # 前端模版渲染内容
    context = {
        'active_page': 'notice',
        'user_id': user_id,
    }
    return render(request, 'create_notice_admin.html', context)

# 通知界面：删除通知
@login_required
def delete_notice(request):
    # 处理POST请求，删除指定的通知
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        try:
            notification = AdminNotification.objects.filter(id=notification_id).first()
            notification.delete()
            return JsonResponse({'status': 'success'}, status=200)
        except AdminNotification.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '通知未找到'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)

# 通知界面：通知内容
@login_required
def notification_content(request):
    # 处理POST请求，获取指定的通知内容
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        notification = AdminNotification.objects.get(id=notification_id)
        return JsonResponse({'title': notification.title, 'content': notification.content}, status=200)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)

# 教师管理
@login_required
def information_administrator(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 获取所有教师信息
    teachers = administrator.teachers.all() if administrator.teachers.exists() else None
    # 前端模版渲染内容
    context = {
        'active_page': 'teachermanage',
        'user_id': user_id,
        'teachers': teachers,
    }
    return render(request, 'information_administrator.html', context)

# 教师管理：添加教师
@login_required
def add_teacher(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 处理POST请求，添加新的教师
    if request.method == 'POST':
        initial_password = request.POST.get('initialPassword')
        file = request.FILES.get('excelFile')
        # 读取Excel文件内容, 并创建新的教师
        if initial_password and file:
            data = pd.read_excel(file)
            for index, row in data.iterrows():
                hashed_password = make_password(initial_password)
                if not isinstance(administrator, Administrator):
                    administrator = Administrator.objects.get(pk=administrator.pk)
                Teacher.objects.create(
                    name=row['姓名'],
                    userid=row['教工号'],
                    course_coordinator=administrator,
                    password=hashed_password,
                )
            return redirect('administrator_app:information_administrator')
    # 前端模版渲染内容
    context = {
        'active_page': 'teachermanage',
        'user_id': user_id,
    }
    return render(request, 'add_teacher.html', context)

# 教师管理：删除教师
@login_required
def delete_teacher(request):
    # 处理POST请求，删除指定的教师
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            teacher.delete()
            return JsonResponse({'status': 'success', 'message': '教师删除成功'}, status=200)
        except Teacher.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '教师未找到'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)

# 教师管理：重置密码
@login_required
def reset_password(request):
    # 处理POST请求，重置指定教师的密码
    if request.method == 'POST':
        teacher = Teacher.objects.get(id=request.POST.get('teacher_id'))
        try:
            initial_password = 'cumt1909'  # 设置为默认密码
            hashed_password = make_password(initial_password)
            teacher.password = hashed_password
            teacher.save()
            return JsonResponse({'status': 'success', 'message': '初始化成功，密码改为cumt1909'}, status=200)
        except Teacher.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '初始化密码失败'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'}, status=400)

# 课程负责人个人中心
@login_required
def profile_administrator(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 前端模版渲染内容
    context = {
        'active_page': 'profile',
        'user_id': user_id,
        'administrator': administrator,
    }
    return render(request, 'profile_administrator.html', context)

# 课程负责人个人中心：修改个人信息
@login_required
def profile_administrator_edit(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 处理POST请求，修改管理员信息
    context = {
        'active_page': 'profile',
        'user_id': user_id,
        'administrator': administrator,
    }
    # 处理POST请求，修改管理员信息
    if request.method == 'POST':
        phone_num = request.POST.get('phone_num')
        email = request.POST.get('email')
        administrator.phone_num = phone_num
        administrator.email = email
        administrator.save()
        return redirect('administrator_app:profile_administrator')
    return render(request, 'profile_administrator_edit.html', context)

# 课程负责人个人中心-修改密码
@login_required
def profile_adminadministrator_password(request):
    administrator = Administrator.objects.get(pk=request.user.pk)
    user_id = administrator.userid
    # 前端模版渲染内容
    context = {
        'active_page': 'profile',
        'user_id': user_id,
    }
    # 处理POST请求，修改密码
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        # 确保旧密码正确
        if check_password(old_password, administrator.password):
            if new_password == confirm_password:
                administrator.password = make_password(new_password)
                administrator.save()
                return JsonResponse({'status': 'success', 'message': '密码修改成功'}, status=200)
            else:
                return JsonResponse({'status': 'error', 'message': '两次输入的密码不一致'}, status=400)
        else:
            return JsonResponse({'status': 'error', 'message': '旧密码错误'}, status=400)
    return render(request, 'password_admin_edit.html', context)



