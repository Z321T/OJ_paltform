from django.db import models
from student_app.models import Student
from teacher_app.models import Class, ExerciseQuestion, ExamQuestion, Exercise, Exam
from administrator_app.models import AdminExam, AdminExamQuestion


class Scores(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="学生", related_name='scores')
    question_type = models.CharField(max_length=20, choices=[('exercise', '练习'), ('exam', '考试'), ('adminexam', '年级考试')], verbose_name="题目类型")
    type_id = models.IntegerField(verbose_name="类型ID") # exercise_id, exam_id, adminexam_id
    question_id = models.IntegerField(verbose_name="题目ID")
    score = models.DecimalField(verbose_name="得分", max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.student.name} - {self.get_question()} - {self.score}"

    def get_question(self):
        if self.question_type == 'exercise':
            return ExerciseQuestion.objects.get(id=self.question_id)
        elif self.question_type == 'exam':
            return ExamQuestion.objects.get(id=self.question_id)
        elif self.question_type == 'adminexam':
            return AdminExamQuestion.objects.get(id=self.question_id)
        return None


class ExerciseCompletion(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="学生",
                                related_name='exercise_completions')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, verbose_name="练习",
                                 related_name='exercise_completions')
    completed_at = models.DateTimeField(verbose_name="完成时间", null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - {self.exercise.title} - 完成: {bool(self.completed_at)}"


class ExerciseQuestionCompletion(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="学生",
                                related_name='exercise_question_completions')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, verbose_name="练习", null=True, blank=True,
                                 related_name='exercise_question_completions')
    exercise_question = models.ForeignKey(ExerciseQuestion, on_delete=models.CASCADE, verbose_name="练习题",
                                          related_name='exercise_question_completions')
    completed_at = models.DateTimeField(verbose_name="完成时间", null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - {self.exercise_question} - 完成: {bool(self.completed_at)}"


class ExamCompletion(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="学生",
                                related_name='exam_completions')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, verbose_name="考试",
                             related_name='exam_completions')
    completed_at = models.DateTimeField(verbose_name="完成时间", null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - {self.exam.title} - 完成: {bool(self.completed_at)}"


class ExamQuestionCompletion(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="学生",
                                related_name='exam_question_completions')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, verbose_name="考试", null=True, blank=True,
                             related_name='exam_question_completions')
    exam_question = models.ForeignKey(ExamQuestion, on_delete=models.CASCADE, verbose_name="考试题",
                                      related_name='exam_question_completions')
    completed_at = models.DateTimeField(verbose_name="完成时间", null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - {self.exam_question} - 完成: {bool(self.completed_at)}"


class AdminExamCompletion(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="学生",
                                related_name='adminexam_completions')
    adminexam = models.ForeignKey(AdminExam, on_delete=models.CASCADE, verbose_name="考试",
                                  related_name='adminexam_completions')
    completed_at = models.DateTimeField(verbose_name="完成时间", null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - {self.adminexam.title} - 完成: {bool(self.completed_at)}"


class AdminExamQuestionCompletion(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="学生",
                                related_name='adminexam_question_completions')
    adminexam = models.ForeignKey(AdminExam, on_delete=models.CASCADE, verbose_name="考试", null=True, blank=True,
                                  related_name='adminexam_question_completions')
    adminexam_question = models.ForeignKey(AdminExamQuestion, on_delete=models.CASCADE, verbose_name="考试题",
                                           related_name='adminexam_question_completions')
    completed_at = models.DateTimeField(verbose_name="完成时间", null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - {self.adminexam_question} - 完成: {bool(self.completed_at)}"


class StudentCode(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="学生",
                                related_name='student_codes')
    code = models.TextField(verbose_name="代码")
    question_type = models.CharField(verbose_name="题目类型", max_length=255, null=True, blank=True)
    question_id = models.CharField(verbose_name="题目id", max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="提交时间", auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} - {self.question_type} - {self.question_id} - {self.created_at}"


class TestResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="学生",
                                related_name='test_results')
    question_type = models.CharField(verbose_name="题目类型", max_length=255, null=True, blank=True)
    question_id = models.CharField(verbose_name="题目id", max_length=255, null=True, blank=True)

    teststatus = models.CharField(max_length=20, null=True, blank=True) # pass, fail, timeout, compile error, other error
    testtype = models.CharField(max_length=20, null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    passed_tests = models.IntegerField(null=True, blank=True)
    testcases = models.IntegerField(default=0, null=True, blank=True)
    execution_time = models.IntegerField(default=0)  # ms
    max_memory = models.IntegerField(default=0)  # KB