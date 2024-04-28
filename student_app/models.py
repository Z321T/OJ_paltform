from django.db import models
from teacher_app.models import Class, ExerciseQuestion, ExamQuestion, Exercise, Exam
from administrator_app.models import AdminExam, AdminExamQuestion


# Create your models here.
class Student(models.Model):
    name = models.CharField(verbose_name="姓名", max_length=6)
    userid = models.CharField(verbose_name="学号", max_length=8)
    password = models.CharField(verbose_name="密码", max_length=128)
    email = models.EmailField(verbose_name="邮箱", unique=True, null=True, blank=True)
    last_login = models.DateTimeField(verbose_name='登录时间', null=True, blank=True)
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name="班级",
                                       null=True, blank=True, related_name='students')


class Score(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="学生", related_name='scores')
    exercise_question = models.ForeignKey(ExerciseQuestion, on_delete=models.CASCADE,
                                          verbose_name="练习题", null=True, blank=True, related_name='scores')
    exam_question = models.ForeignKey(ExamQuestion, on_delete=models.CASCADE,
                                      verbose_name="考试题", null=True, blank=True, related_name='scores')
    adminexam_question = models.ForeignKey(AdminExamQuestion, on_delete=models.CASCADE,
                                           verbose_name="年级考试题", null=True, blank=True, related_name='scores')
    score = models.DecimalField(verbose_name="得分", max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.student.name} - {self.exercise_question or self.exam_question or self.adminexam_question} - {self.score}"


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
    adminexam_question = models.ForeignKey(AdminExamQuestion, on_delete=models.CASCADE, verbose_name="考试题",
                                           related_name='adminexam_question_completions')
    completed_at = models.DateTimeField(verbose_name="完成时间", null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - {self.adminexam_question} - 完成: {bool(self.completed_at)}"

