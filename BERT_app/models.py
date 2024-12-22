from django.db import models

from administrator_app.models import ProgrammingExercise
from student_app.models import Student
from teacher_app.models import ExerciseQuestion, ExamQuestion


class ProgrammingCodeFeature(models.Model):
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, verbose_name="学生",
                                related_name='programming_code_features', null=True)
    programming_question = models.ForeignKey(ProgrammingExercise, on_delete=models.CASCADE, verbose_name="练习题",
                                             related_name='programming_code_features', null=True, blank=True)
    feature = models.TextField(verbose_name="特征值")
    cosine_similarity = models.FloatField(verbose_name="余弦相似度", null=True, blank=True)
    similar_student = models.ForeignKey(Student, on_delete=models.SET_NULL, verbose_name="相似的学生用户",
                                        related_name='similar_code_students', null=True, blank=True)

    def __str__(self):
        return (f"{self.student.name if self.student else '无关联学生'} - "
                f"{self.programming_question} - {self.feature}")


class ProgrammingReportFeature(models.Model):
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, verbose_name="学生",
                                related_name='programming_report_features', null=True)
    programming_question = models.ForeignKey(ProgrammingExercise, on_delete=models.CASCADE, verbose_name="练习题",
                                             related_name='programming_report_features', null=True, blank=True)
    feature = models.TextField(verbose_name="特征值")
    cosine_similarity = models.FloatField(verbose_name="余弦相似度", null=True, blank=True)
    similar_student = models.ForeignKey(Student, on_delete=models.SET_NULL, verbose_name="相似的学生用户",
                                        related_name='similar_report_students', null=True, blank=True)

    def __str__(self):
        return (f"{self.student.name if self.student else '无关联学生'} - "
                f"{self.programming_question} - {self.feature}")


class ReportStandardScore(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="学生",
                                related_name='report_standards')
    programming_question = models.ForeignKey(ProgrammingExercise, on_delete=models.CASCADE, verbose_name="练习题",
                                             related_name='report_standards')
    standard_score = models.IntegerField(verbose_name="报告规范性得分")

