from django.db import models

from teacher_app.models import Exam, ExamQuestion
from administrator_app.models import AdminExam, AdminExamQuestion


# Create your models here.
class ClassExamSubmission(models.Model):
    submission_id = models.CharField(verbose_name="提交编号", max_length=255, blank=True, null=True)
    student_id = models.CharField(verbose_name="学号", max_length=20)
    exam = models.ForeignKey(Exam, verbose_name="考试", on_delete=models.CASCADE)
    question = models.ForeignKey(ExamQuestion, verbose_name="考试题目", on_delete=models.CASCADE)
    result = models.CharField(verbose_name="结果", max_length=10)
    memory = models.IntegerField(verbose_name="内存")
    time = models.IntegerField(verbose_name="耗时")
    language = models.CharField(verbose_name="语言", max_length=10)
    code_length = models.IntegerField(verbose_name="代码长度")
    ip_address = models.CharField(verbose_name="IP地址", max_length=45, blank=True, null=True)
    submission_time = models.DateTimeField(verbose_name="提交时间")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.submission_id:
            self.submission_id = self.id
            self.save()

    def __str__(self):
        return f"{self.submission_id} - {self.student_id}"


class GradeExamSubmission(models.Model):
    submission_id = models.CharField(verbose_name="提交编号", max_length=255, blank=True, null=True)
    student_id = models.CharField(verbose_name="学号", max_length=20)
    exam = models.ForeignKey(AdminExam, verbose_name="考试", on_delete=models.CASCADE)
    question = models.ForeignKey(AdminExamQuestion, verbose_name="考试题目", on_delete=models.CASCADE)
    result = models.CharField(verbose_name="结果", max_length=10)
    memory = models.IntegerField(verbose_name="内存")
    time = models.IntegerField(verbose_name="耗时")
    language = models.CharField(verbose_name="语言", max_length=10)
    code_length = models.IntegerField(verbose_name="代码长度")
    ip_address = models.CharField(verbose_name="IP地址", max_length=45, blank=True, null=True)
    submission_time = models.DateTimeField(verbose_name="提交时间")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.submission_id:
            self.submission_id = self.id
            self.save()

    def __str__(self):
        return f"{self.submission_id} - {self.student_id}"
